<template>
  <div>
    <Header v-bind:isUploadActive=true></Header>
    <br>
    <b-container class="bv-example-row">
      <b-alert
          :show="dismissCountDown"
          dismissible variant="danger"
          @dismissed="dismissCountDown=0"
          @dismiss-count-down="countDownChanged"
      >{{ errorMessage }}</b-alert>
      <h1>Upload Videos</h1>
      <p v-html="marked(description)"></p>
      <vue-dropzone ref="myVueDropzone" id="dropzone" :awss3="awss3" v-on:vdropzone-s3-upload-error="s3UploadError" v-on:vdropzone-success="s3UploadComplete" :options="dropzoneOptions">
      </vue-dropzone>
      <hr>
      <label>Upload destination:</label>
      <span class="note"> {{ s3_destination }} </span><br>
      <b-button variant="primary" @click="uploadFiles">Start</b-button>
    </b-container>
    <br>
    <b-container class="bv-example-row">
      <b-table striped bordered hover small responsive fixed :items="executed_assets"></b-table>
    </b-container>
  </div>
</template>

<script>
import vueDropzone from '@/components/vue-dropzone.vue';
import Header from '@/components/Header.vue'

export default {
  data() {
    return {
      errorMessage: "",
      dismissSecs: 8,
      dismissCountDown: 0,
      executed_assets: [],
      workflow_status_polling: null,
      description: "Click start to begin. Media analysis status will be shown after upload completes.",
      signurl: process.env.VUE_APP_DATAPLANE_API_ENDPOINT+'/upload',
      s3_destination: 's3://'+process.env.VUE_APP_DATAPLANE_BUCKET,
      dropzoneOptions: {
        url: 'https://'+process.env.VUE_APP_DATAPLANE_BUCKET+'.s3-us-west-2.amazonaws.com',
        thumbnailWidth: 200,
        addRemoveLinks: true,
        autoProcessQueue: false,
      },
      awss3: {
        signingURL: '',
        headers: {},
        params : {}
      }
    }
  },
  methods: {
    countDownChanged(dismissCountDown) {
      this.dismissCountDown = dismissCountDown
    },
    s3UploadError(error) {
      console.log(error);
      // display alert
      this.errorMessage = error;
      this.dismissCountDown = this.dismissSecs;
    },
    s3UploadComplete: function (location) {
      var vm = this;
      var s3_uri = location.s3ObjectLocation.url + location.s3ObjectLocation.fields.key
      var media_type = location.type;
      console.log('media type: ' + media_type)
      console.log('s3UploadComplete: ')
      console.log(s3_uri)
      var data = {}
      if (media_type == 'image/jpeg') {
        data = {
          "Name": "ParallelRekognitionWorkflowImage",
          "Configuration": {
            "parallelRekognitionStageImage": {
              "faceSearchImage": {
                "MediaType": "Image",
                "Enabled": false,
              },
              "labelDetectionImage": {"MediaType": "Image", "Enabled": true},
              "celebrityRecognitionImage": {"MediaType": "Image", "Enabled": true},
              "contentModerationImage": {"MediaType": "Image", "Enabled": true},
              "faceDetectionImage": {"MediaType": "Image", "Enabled": true}
            }
          },
          "Input": {
            "Media": {
              "Image": {
                "S3Bucket": process.env.VUE_APP_DATAPLANE_BUCKET,
                "S3Key": location.s3ObjectLocation.fields.key
              }
            }
          }
        };
      } else if (media_type == 'video/mp4') {
        data = {
          "Name": "MieCompleteWorkflow",
          "Configuration": {
            "defaultVideoStage": {
              "faceSearch": {
                "MediaType": "Video",
                "Enabled": false
              }
            }
          },
          "Input": {
            "Media": {
              "Video": {
                "S3Bucket": process.env.VUE_APP_DATAPLANE_BUCKET,
                "S3Key": location.s3ObjectLocation.fields.key
              }
            }
          }
        };
      } else {
        vm.s3UploadError("Unsupported media type, " + media_type + ". Please upload a jpg or mp4.")
      }
      fetch(process.env.VUE_APP_WORKFLOW_API_ENDPOINT + 'workflow/execution', {
        method: 'post',
        body: JSON.stringify(data),
        headers: {'Content-Type': 'application/json'}
      }).then(response =>
        response.json().then(data => ({
            data: data,
            status: response.status
          })
        ).then(res => {
          if (res.status != 200) {
            console.log("ERROR: Failed to start workflow")
          } else {
            var asset_id = res.data.AssetId;
            var s3key = location.s3ObjectLocation.fields.key;
            console.log("Media assigned asset id: " + asset_id);
            vm.executed_assets.push({asset_id: asset_id, file_name: s3key, workflow_status: ""});
            vm.getWorkflowStatus(asset_id);
            vm.pollWorkflowStatus()
          }
        })
      )
    },
    getWorkflowStatus(asset_id) {
      var vm = this;
      fetch(process.env.VUE_APP_WORKFLOW_API_ENDPOINT+'workflow/execution/asset/'+asset_id, {
        method: 'get',
      }).then(response =>
        response.json().then(data => ({
            data: data,
            status: response.status
          })
        ).then(res => {
          if (res.status != 200) {
            console.log("ERROR: Failed to get workflow status")
          } else {
            for (var i = 0; i < vm.executed_assets.length; i++) {
              if (vm.executed_assets[i].asset_id === asset_id) {
                vm.executed_assets[i].workflow_status = res.data[0].Status;
                break;
              }
            }
          }
        })
      )
    },
    pollWorkflowStatus() {
      // Poll frequency in milliseconds
      const poll_frequency = 5000
      this.workflow_status_polling = setInterval(() => {
        this.executed_assets.forEach(item => {
          if (item.workflow_status === "" || item.workflow_status === "Started" || item.workflow_status === "Queued") {
            this.getWorkflowStatus(item.asset_id)
          }
        });
      }, poll_frequency)
    },
    uploadFiles() {
      if (this.signurl) {
        this.$refs.myVueDropzone.setAWSSigningURL(this.signurl);
        this.$refs.myVueDropzone.processQueue();
      }
      else {
        this.$refs.urlsigner.focus();
        alert("Enter your signing URL");
      }
    }
  },
  beforeDestroy () {
    clearInterval(this.workflow_status_polling)
  },
  components: {
    vueDropzone,
    Header
  }
}
</script>
<style>
input[type=text] {
  width: 100%;
  padding: 12px 20px;
  margin: 8px 0;
  box-sizing: border-box;
}

label {
  font-weight: bold;
}

.note {
  color: red;
  font-family: "Courier New"
}
</style>
