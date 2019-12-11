<template>
  <div>
    <Header :is-upload-active="true" />
    <br>
    <b-container>
      <b-alert
        :show="dismissCountDown"
        dismissible
        variant="danger"
        @dismissed="dismissCountDown=0"
        @dismiss-count-down="countDownChanged"
      >
        {{ uploadErrorMessage }}
      </b-alert>
      <h1>Upload Videos</h1>
      <p>{{ description }}</p>
      <vue-dropzone
        id="dropzone"
        ref="myVueDropzone"
        :awss3="awss3"
        :options="dropzoneOptions"
        @vdropzone-s3-upload-error="s3UploadError"
        @vdropzone-success="s3UploadComplete"
        @vdropzone-sending="upload_in_progress=true"
        @vdropzone-queue-complete="upload_in_progress=false"
      />
      <br>
      <b-button v-b-toggle.collapse-2 class="m-1">
        Configure Workflow
      </b-button>
      <b-button v-if="validForm" variant="primary" @click="uploadFiles">
        Start Upload and Run Workflow
      </b-button>
      <b-button v-else disabled variant="primary" @click="uploadFiles">
        Start Upload and Run Workflow
      </b-button>
      <br>
      <span v-if="upload_in_progress" class="text-secondary">Upload in progress</span>
      <b-container v-if="upload_in_progress">
        <b-spinner label="upload_in_progress" />
      </b-container>
      <br>
      <b-collapse id="collapse-2">
        <b-container class="text-left">
          <b-card-group deck>
            <b-card header="Video and Image Operators">
              <b-form-group>
                <b-form-checkbox-group
                  id="checkbox-group-1"
                  v-model="enabledOperators"
                  :options="videoOperators"
                  name="flavour-1"
                ></b-form-checkbox-group>
                <label>Thumbnail position: </label>
                <b-form-input v-model="thumbnail_position" type="range" min="1" max="20" step="1"></b-form-input> {{ thumbnail_position }} sec
                <b-form-input v-if="enabledOperators.includes('faceSearch')" id="Enter face collection id" v-model="faceCollectionId"></b-form-input>

                <b-form-input v-if="enabledOperators.includes('genericDataLookup')" v-model="genericDataFilename" placeholder="Enter data filename"></b-form-input>
              </b-form-group>
              <div v-if="videoFormError" style="color:red">
                {{ videoFormError }}
              </div>
            </b-card>
            <b-card header="Audio Operators">
              <b-form-group>
                <b-form-checkbox-group
                  id="checkbox-group-2"
                  v-model="enabledOperators"
                  :options="audioOperators"
                  name="flavour-2"
                ></b-form-checkbox-group>
                <div v-if="enabledOperators.includes('Transcribe')">
                  <label>Source Language</label>
                  <b-form-select v-model="transcribeLanguage" :options="transcribeLanguages"></b-form-select>
                </div>
              </b-form-group>
              <div v-if="audioFormError" style="color:red">
                {{ audioFormError }}
              </div>
            </b-card>
            <b-card header="Text Operators">
              <b-form-group>
                <b-form-checkbox-group
                  id="checkbox-group-3"
                  v-model="enabledOperators"
                  :options="textOperators"
                  name="flavour-3"
                ></b-form-checkbox-group>
                <div v-if="enabledOperators.includes('Translate')">
                  <label>Translation Source Language</label>
                  <b-form-select v-model="transcribeLanguage" :options="transcribeLanguages"></b-form-select>
                  <label>Translation Target Language</label>
                  <b-form-select v-model="targetLanguageCode" :options="translateLanguages"></b-form-select>
                </div>
              </b-form-group>
              <div v-if="textFormError" style="color:red">
                {{ textFormError }}
              </div>
            </b-card>
          </b-card-group>
          <div align="right">
            <button type="button" class="btn btn-link" @click="selectAll">Select All</button>
            <button type="button" class="btn btn-link" @click="clearAll">Clear All</button>
          </div>
        </b-container>
      </b-collapse>
    </b-container>
    <b-container v-if="executed_assets.length > 0">
      <label>
        Execution History
      </label>
      <b-table
        :fields="fields"
        bordered
        hover
        small
        responsive
        show-empty
        fixed
        :items="executed_assets"
      >
        <template v-slot:cell(workflow_status)="data">
          <a href="" @click.stop.prevent="openWindow(data.item.state_machine_console_link)">{{ data.item.workflow_status }}</a>
        </template>
      </b-table>
      <b-button size="sm" @click="clearHistory">
        Clear History
      </b-button>
    </b-container>
  </div>
</template>

<script>
  import vueDropzone from '@/components/vue-dropzone.vue';
  import Header from '@/components/Header.vue'
  import { mapState } from 'vuex'

  export default {
    components: {
      vueDropzone,
      Header
    },
    data() {
      return {
        fields: [
          {
            'asset_id': {
              label: "Asset Id",
              sortable: false
            }
          },
          {
            'file_name': {
              label: "File Name",
              sortable: false
            }
          },
          { 'workflow_status': {
              label: 'Workflow Status',
              sortable: false
            }
          }
        ],
        thumbnail_position: 10,
        upload_in_progress: false,
        enabledOperators: ['labelDetection', 'celebrityRecognition', 'contentModeration', 'faceDetection', 'thumbnail', 'Transcribe', 'Translate', 'ComprehendKeyPhrases', 'ComprehendEntities'],
        videoOperators: [
          {text: 'Object Detection', value: 'labelDetection'},
          {text: 'Celebrity Recognition', value: 'celebrityRecognition'},
          {text: 'Content Moderation', value: 'contentModeration'},
          {text: 'Face Detection', value: 'faceDetection'},
          {text: 'Face Search', value: 'faceSearch'},
          {text: 'Generic Data Lookup (video only)', value: 'genericDataLookup'},
        ],
        audioOperators: [
          {text: 'Transcribe', value: 'Transcribe'},
        ],
        textOperators: [
          {text: 'Comprehend Key Phrases', value: 'ComprehendKeyPhrases'},
          {text: 'Comprehend Entities', value: 'ComprehendEntities'},
          {text: 'Translate', value: 'Translate'},
        ],
        faceCollectionId: "",
        genericDataFilename: "",
        transcribeLanguage: "en-US",
        transcribeLanguages: [
          {text: 'Arabic, Modern Standard', value: 'ar-SA'},
          {text: 'Chinese', value: 'zh-CN'},
          {text: 'English, US', value: 'en-US'},
          {text: 'English, Australian', value: 'en-AU'},
          {text: 'English, British', value: 'en-GB'},
          {text: 'English, Indian-accented', value: 'en-IN'},
          {text: 'French', value: 'fr-FR'},
          {text: 'French, Canadian', value: 'fr-CA'},
          {text: 'German', value: 'de-DE'},
          {text: 'Hindi', value: 'hi-IN'},
          {text: 'Italian', value: 'it-IT'},
          {text: 'Korean', value: 'ko-KR'},
          {text: 'Portuguese, Brazilian', value: 'pt-BR'},
          {text: 'Russian', value: 'ru-RU'},
          {text: 'Spanish, ES', value: 'es-ES'},
          {text: 'Spanish, US', value: 'es-US'},
        ],
        translateLanguages: [
          {text: 'Arabic', value: 'ar'},
          {text: 'Chinese (Simplified)', value: 'zh'},
          {text: 'Chinese (Traditional)', value: 'zh-TW'},
          {text: 'Czech', value: 'cs'},
          {text: 'Danish', value: 'da'},
          {text: 'Dutch', value: 'nl'},
          {text: 'English', value: 'en'},
          {text: 'Finnish', value: 'fi'},
          {text: 'French', value: 'fr'},
          {text: 'German', value: 'de'},
          {text: 'Hebrew', value: 'he'},
          {text: 'Hindi', value: 'hi'},
          {text: 'Indonesian', value: 'id'},
          {text: 'Italian', value: 'it'},
          {text: 'Japanese', value: 'ja'},
          {text: 'Korean', value: 'ko'},
          {text: 'Malay', value: 'ms'},
          {text: 'Norwegian', value: 'no'},
          {text: 'Persian', value: 'fa'},
          {text: 'Polish', value: 'pl'},
          {text: 'Portuguese', value: 'pt'},
          {text: 'Russian', value: 'ru'},
          {text: 'Spanish', value: 'es'},
          {text: 'Swedish', value: 'sv'},
          {text: 'Turkish', value: 'tr'},
        ],
        sourceLanguageCode: "en",
        targetLanguageCode: "es",
        uploadErrorMessage: "",
        dismissSecs: 8,
        dismissCountDown: 0,
        executed_assets: [],
        workflow_status_polling: null,
        description: "Click start to begin. Media analysis status will be shown after upload completes.",
        signurl: process.env.VUE_APP_DATAPLANE_API_ENDPOINT + '/upload',
        s3_destination: 's3://' + process.env.VUE_APP_DATAPLANE_BUCKET,
        dropzoneOptions: {
          url: 'https://' + process.env.VUE_APP_DATAPLANE_BUCKET + '.s3.amazonaws.com',
          thumbnailWidth: 200,
          addRemoveLinks: true,
          autoProcessQueue: false,
          // disable network timeouts (important for large uploads)
          timeout: 0,
          // limit max upload file size (in MB)
          maxFilesize: 2000
        },
        awss3: {
          signingURL: '',
          headers: {},
          params: {}
        }
      }
    },
    computed: {
      ...mapState(['execution_history']),
      textFormError() {
        return "";
      },
      audioFormError() {
        // Validate transcribe is enabled if any text operator is enabled
        if (!this.enabledOperators.includes("Transcribe") && (this.enabledOperators.includes("Translate") || this.enabledOperators.includes("ComprehendEntities") || this.enabledOperators.includes("ComprehendKeyPhrases"))) {
          return "Transcribe must be enabled if any text operator is enabled.";
        }
        return "";
      },
      videoFormError() {
        // Validate face collection ID if face search is enabled
        if (this.enabledOperators.includes("faceSearch")) {
          // Validate that the collection ID is defined
          if (this.faceCollectionId === "") {
            return "Face collection name is required.";
          }

          // Validate that the collection ID matches required regex
          else if ((new RegExp('[^a-zA-Z0-9_.\\-]')).test(this.faceCollectionId)) {
            return "Face collection name must match pattern [a-zA-Z0-9_.\\\\-]+";
          }
          // Validate that the collection ID is not too long
          else if (this.faceCollectionId.length > 255) {
            return "Face collection name must have fewer than 255 characters.";
          }
        }
        if (this.enabledOperators.includes("genericDataLookup")) {
          // Validate that the collection ID is defined
          if (this.genericDataFilename === "") {
            return "Data filename is required.";
          }
          // Validate that the collection ID matches required regex
          else if (!(new RegExp('^.+\\.json$')).test(this.genericDataFilename)) {
            return "Data filename must have .json extension.";
          }
          // Validate that the data filename is not too long
          else if (this.genericDataFilename.length > 255) {
            return "Data filename must have fewer than 255 characters.";
          }
        }
        return "";
      },
      validForm() {
        var validStatus = true;
        if (this.textFormError || this.audioFormError || this.videoFormError) validStatus = false;
        return validStatus;
      },
      workflowConfig() {
        return {
          "Name": "MieCompleteWorkflow",
          "Configuration": {
            "defaultVideoStage": {
              "faceDetection": {
                "Enabled": this.enabledOperators.includes("faceDetection"),
              },
              "celebrityRecognition": {
                "Enabled": this.enabledOperators.includes("celebrityRecognition"),
              },
              "labelDetection": {
                "Enabled": this.enabledOperators.includes("labelDetection"),
              },
              "Mediaconvert": {
                "Enabled": (this.enabledOperators.includes("Mediaconvert") || this.enabledOperators.includes("Transcribe") || this.enabledOperators.includes("Translate") || this.enabledOperators.includes("ComprehendEntities") || this.enabledOperators.includes("ComprehendKeyPhrases")),
              },
              "contentModeration": {
                "Enabled": this.enabledOperators.includes("contentModeration"),
              },
              "faceSearch": {
                "Enabled": this.enabledOperators.includes("faceSearch"),
                "CollectionId": this.faceCollectionId==="" ? "undefined" : this.faceCollectionId
              },
              "personTracking": {
                // TODO: enable this operator after it has been added to front-end
                "Enabled": false,
              },
              "GenericDataLookup": {
                "Enabled": this.enabledOperators.includes("genericDataLookup"),
                "Bucket": process.env.VUE_APP_DATAPLANE_BUCKET,
                "Key": this.genericDataFilename==="" ? "undefined" : this.genericDataFilename
              },
              "Thumbnail": {
                "ThumbnailPosition": this.thumbnail_position.toString(),
                "Enabled": true
              }
            },
            "defaultAudioStage": {
              "Transcribe": {
                "Enabled": this.enabledOperators.includes("Transcribe"),
                "TranscribeLanguage": this.transcribeLanguage
              }

            },
            "defaultTextStage": {
              "Translate": {
                "Enabled": this.enabledOperators.includes("Translate"),
                "SourceLanguageCode": this.transcribeLanguage.split('-')[0],
                "TargetLanguageCode": this.targetLanguageCode
              },
              "ComprehendEntities": {
                "Enabled": this.enabledOperators.includes("ComprehendEntities"),
              },
              "ComprehendKeyPhrases": {
                "Enabled": this.enabledOperators.includes("ComprehendKeyPhrases"),
              }

            },
            "defaultTextSynthesisStage": {
              // Polly is available in the MIECompleteWorkflow but not used in the front-end, so we've disabled it here.
              "Polly": {
                "Enabled": false,
              }
            }
          },
        }
      }
    },
    mounted: function() {
      this.executed_assets = this.execution_history;
      this.pollWorkflowStatus()
    },
    beforeDestroy () {
      clearInterval(this.workflow_status_polling)
    },
    methods: {
      selectAll: function (){
        this.enabledOperators = ['labelDetection', 'celebrityRecognition', 'contentModeration', 'faceDetection', 'thumbnail', 'Transcribe', 'Translate', 'ComprehendKeyPhrases', 'ComprehendEntities']
      },
      clearAll: function (){
        this.enabledOperators = []
      },
      openWindow: function (url) {
        window.open(url);
      },
      countDownChanged(dismissCountDown) {
        this.dismissCountDown = dismissCountDown
      },
      s3UploadError(error) {
        console.log(error);
        // display alert
        this.uploadErrorMessage = error;
        this.dismissCountDown = this.dismissSecs;
      },
      s3UploadComplete: async function (location) {
        const token = await this.$Amplify.Auth.currentSession().then(data =>{
          var accessToken = data.getIdToken().getJwtToken();
          return accessToken
        });
        var vm = this;
        var s3_uri = location.s3ObjectLocation.url + location.s3ObjectLocation.fields.key;
        var media_type = location.type;
        console.log('media type: ' + media_type);
        console.log('s3UploadComplete: ');
        console.log(s3_uri)
        var data = {}
        if (media_type == 'image/jpeg') {
          data = {
            "Name": "ImageWorkflow",
            "Configuration": {
              "RekognitionStage": {
                "faceSearchImage": {
                  "Enabled": this.enabledOperators.includes("faceSearch"),
                  "CollectionId": this.faceCollectionId === "" ? "undefined" : this.faceCollectionId
                },
                "labelDetectionImage": {
                  "Enabled": this.enabledOperators.includes("labelDetection"),
                },
                "celebrityRecognitionImage": {
                  "Enabled": this.enabledOperators.includes("celebrityRecognition"),
                },
                "contentModerationImage": {
                  "Enabled": this.enabledOperators.includes("contentModeration"),
                },
                "faceDetectionImage": {
                  "Enabled": this.enabledOperators.includes("faceDetection"),
                }
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
          data = vm.workflowConfig;
          data["Input"] = {
            "Media": {
              "Video": {
                "S3Bucket": process.env.VUE_APP_DATAPLANE_BUCKET,
                "S3Key": location.s3ObjectLocation.fields.key
              }
            }
          };
        } else if (media_type == 'application/json') {
          // JSON files may be uploaded for the genericDataLookup operator, but
          // we won't run a workflow for json file types.
          console.log("Data file has been uploaded to s3://" + location.s3ObjectLocation.fields.key)
          return;
        } else {
          vm.s3UploadError("Unsupported media type, " + media_type + ". Please upload a jpg or mp4.")
        }
        console.log(JSON.stringify(data))
        fetch(process.env.VUE_APP_WORKFLOW_API_ENDPOINT + 'workflow/execution', {
          method: 'post',
          body: JSON.stringify(data),
          headers: {'Content-Type': 'application/json', 'Authorization': token}
        }).then(response =>
          response.json().then(data => ({
              data: data,
              status: response.status
            })
          ).then(res => {
            if (res.status != 200) {
              console.log("ERROR: Failed to start workflow.");
              console.log(res.data.Code);
              console.log(res.data.Message);
              console.log("URL: " + process.env.VUE_APP_WORKFLOW_API_ENDPOINT + 'workflow/execution');
              console.log("Data:");
              console.log(JSON.stringify(data));
              console.log((data));
              console.log("Response: " + response.status);
            } else {
              var asset_id = res.data.AssetId;
              var s3key = location.s3ObjectLocation.fields.key;
              console.log("Media assigned asset id: " + asset_id);
              vm.executed_assets.push({asset_id: asset_id, file_name: s3key, workflow_status: "", state_machine_console_link: ""});
              vm.getWorkflowStatus(asset_id);
            }
          })
        )
      },
      async getWorkflowStatus(asset_id) {
        const token = await this.$Amplify.Auth.currentSession().then(data =>{
          var accessToken = data.getIdToken().getJwtToken()
          return accessToken
        })
        var vm = this;
        fetch(process.env.VUE_APP_WORKFLOW_API_ENDPOINT+'workflow/execution/asset/'+asset_id, {
          method: 'get',
          headers: {
            'Authorization': token
          }
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
                  vm.executed_assets[i].state_machine_console_link = "https://"+process.env.VUE_APP_AWS_REGION+".console.aws.amazon.com/states/home?region="+process.env.VUE_APP_AWS_REGION+"#/executions/details/"+res.data[0].StateMachineExecutionArn;
                  break;
                }
              }
              this.$store.commit('updateExecutedAssets', vm.executed_assets);
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
        console.log("Uploading to " + this.s3_destination);
        // console.log("Presigning URL endpoint: " + this.signurl);
        this.$refs.myVueDropzone.setAWSSigningURL(this.signurl);
        this.$refs.myVueDropzone.processQueue();
      },
      clearHistory() {
        this.executed_assets = [];
        this.$store.commit('updateExecutedAssets', this.executed_assets);

      }
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
