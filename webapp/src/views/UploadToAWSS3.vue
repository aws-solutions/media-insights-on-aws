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
                <b-form-input v-if="enabledOperators.includes('faceSearch')" v-model="faceCollectionId" placeholder="Enter face collection id"></b-form-input>
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
                  <b-form-select v-model="sourceLanguageCode" :options="translateLanguages"></b-form-select>
                  <label>Translation Target Language</label>
                  <b-form-select v-model="targetLanguageCode" :options="translateLanguages"></b-form-select>
                </div>
              </b-form-group>
              <div v-if="textFormError" style="color:red">
                {{ textFormError }}
              </div>
            </b-card>
          </b-card-group>
        </b-container>
      </b-collapse>
    </b-container>
    <br>
    <b-container class="bv-example-row">
      <b-table
        striped
        bordered
        hover
        small
        responsive
        fixed
        :items="executed_assets"
      />
    </b-container>
  </div>
</template>

<script>
  import vueDropzone from '@/components/vue-dropzone.vue';
  import Header from '@/components/Header.vue'

  export default {
    components: {
      vueDropzone,
      Header
    },
    data() {
      return {
        upload_in_progress: false,
        enabledOperators: ['labelDetection', 'celebrityRecognition', 'contentModeration', 'faceDetection', 'Transcribe', 'Translate', 'ComprehendKeyPhrases', 'ComprehendEntities'],
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
          {text: 'Polly', value: 'Polly'},
          {text: 'Translate', value: 'Translate'},
        ],
        faceCollectionId: "",
        genericDataFilename: "",
        transcribeLanguage: "en-US",
        transcribeLanguages: [
          {text: 'US English', value: 'en-US'},
          {text: 'British English', value: 'en-GB'},
          {text: 'Australian English', value: 'en-AU'},
          {text: 'French', value: 'fr-FR'},
          {text: 'Canadian French', value: 'fr-CA'},
          {text: 'US Spanish', value: 'es-US'},
          {text: 'ES Spanish', value: 'es-ES'},
          {text: 'Italian', value: 'it-IT'},
          {text: 'Brazilian Portuguese', value: 'pt-BR'},
          {text: 'German', value: 'de-DE'},
          {text: 'Korean', value: 'ko-KR'},
          {text: 'Hindi', value: 'hi-IN'},
          {text: 'Indian-accented English', value: 'en-IN'},
          {text: 'Modern Standard Arabic', value: 'ar-SA'},
          {text: 'Russian', value: 'ru-RU'},
          {text: 'Chinese', value: 'zh-CN'},
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
        targetLanguageCode: "ru",
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
          maxFilesize: 500
        },
        awss3: {
          signingURL: '',
          headers: {},
          params: {}
        }
      }
    },
    computed: {
      textFormError() {
        // Validate translated text is en, ru, es, or fr if Polly is enabled
        if (this.enabledOperators.includes('Polly') && !(this.enabledOperators.includes('Translate'))) {
          return "Polly requires Translate to be enabled.";
        }
        if (this.enabledOperators.includes('Polly') && this.targetLanguageCode !== "en" && this.targetLanguageCode !== "ru" && this.targetLanguageCode !== "es" && this.targetLanguageCode !== "fr") {
          return "Polly requires translation target to be English, Russian, Spanish, or French.";
        }
        return "";
      },
      audioFormError() {
        // Validate transcribe is enabled if any text operator is enabled
        if (!this.enabledOperators.includes("Transcribe") && (this.enabledOperators.includes("Translate") || this.enabledOperators.includes("ComprehendEntities") || this.enabledOperators.includes("ComprehendKeyPhrases") || this.enabledOperators.includes("Polly"))) {
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
                "Enabled": (this.enabledOperators.includes("Mediaconvert") || this.enabledOperators.includes("Transcribe") || this.enabledOperators.includes("Translate") || this.enabledOperators.includes("ComprehendEntities") || this.enabledOperators.includes("ComprehendKeyPhrases") || this.enabledOperators.includes("Polly")),
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
                "SourceLanguageCode": this.sourceLanguageCode,
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
              "Polly": {
                "Enabled": this.enabledOperators.includes("Polly"),
              }

            }
          },
        }
      }
    },
    beforeDestroy () {
      clearInterval(this.workflow_status_polling)
    },
    methods: {
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
              vm.executed_assets.push({asset_id: asset_id, file_name: s3key, workflow_status: ""});
              vm.getWorkflowStatus(asset_id);
              vm.pollWorkflowStatus()
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
        console.log("Uploading to " + this.s3_destination);
        // console.log("Presigning URL endpoint: " + this.signurl);
        this.$refs.myVueDropzone.setAWSSigningURL(this.signurl);
        this.$refs.myVueDropzone.processQueue();
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
