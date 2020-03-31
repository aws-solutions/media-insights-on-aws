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
      <b-alert
          :show="showInvalidFile"
          variant="danger"
      >
        {{ invalidFileMessages[invalidFileMessages.length-1] }}
      </b-alert>
      <h1>Upload Videos</h1>
      <p>{{ description }}</p>
      <vue-dropzone
          id="dropzone"
          ref="myVueDropzone"
          :awss3="awss3"
          :options="dropzoneOptions"
          @vdropzone-s3-upload-error="s3UploadError"
          @vdropzone-file-added="fileAdded"
          @vdropzone-removed-file="fileRemoved"
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
                  <b-form-group>
                    <voerro-tags-input element-id="target_language_tags"
                                       v-model="selectedTranslateLanguages"
                                       :limit=10
                                       :hide-input-on-limit="true"
                                       :existing-tags=translateLanguageTags
                                       :only-existing-tags="true"
                                       :add-tags-on-space="true"
                                       :add-tags-on-comma="true"
                                       :add-tags-on-blur="true"
                                       :sort-search-results="true"
                                       :typeahead-always-show="true"
                                       :typeahead-hide-discard="true"
                                       :typeahead="true">
                    </voerro-tags-input>
                  </b-form-group>
                </div>
              </b-form-group>
              <div v-if="textFormError" style="color:red">
                {{ textFormError }}
              </div>
            </b-card>
            <b-card header="Video Distribution">
              <b-form-group>
                <b-form-checkbox
                    v-model="create_video_stream"
                    value="true"
                    unchecked-value="false"
                >
                  Create video stream
                </b-form-checkbox>
                <b-form-checkbox
                    v-model="show_disclaimer"
                    value="true"
                    unchecked-value="false"
                >
                  Show "Not Reviewed" disclaimer
                </b-form-checkbox>
              </b-form-group>
            </b-card>
          </b-card-group>
          <div align="right">
            <button type="button" class="btn btn-link" @click="selectAll">
              Select All
            </button>
            <button type="button" class="btn btn-link" @click="clearAll">
              Clear All
            </button>
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
  import VoerroTagsInput from '@/components/VoerroTagsInput.vue';
  import '@/components/VoerroTagsInput.css';

  import { mapState } from 'vuex'

  export default {
    components: {
      vueDropzone,
      Header,
      VoerroTagsInput
    },
    data() {
      return {
        selectedTags: [
        ],
        show_disclaimer: true,
        create_video_stream: true,
        valid_media_types: ['cmaf', 'dash', 'hls', 'mp4', 'f4v', 'mxf', 'mov', 'ismv', 'raw', 'av1', 'avc', 'hevc', 'mpeg-2', 'avi', 'mkv', 'webm'], // see https://docs.aws.amazon.com/mediaconvert/latest/ug/reference-codecs-containers.html
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
        enabledOperators: ['thumbnail', 'Transcribe', 'Translate'],
        videoOperators: [
          {text: 'Object Detection', value: 'labelDetection'},
          {text: 'Celebrity Recognition', value: 'celebrityRecognition'},
          {text: 'Content Moderation', value: 'contentModeration'},
          {text: 'Face Detection', value: 'faceDetection'},
          {text: 'Word Detection', value: 'textDetection'},
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
          {text: 'Arabic, Gulf', value: 'ar-AE'},
          {text: 'Arabic, Modern Standard', value: 'ar-SA'},
          {text: 'Chinese Mandarin', value: 'zh-CN'},
          {text: 'Dutch', value: 'nl-NL'},
          {text: 'English, Australian', value: 'en-AU'},
          {text: 'English, British', value: 'en-GB'},
          {text: 'English, Indian-accented', value: 'en-IN'},
          {text: 'English, Irish', value: 'en-IE'},
          {text: 'English, Scottish', value: 'en-AB'},
          {text: 'English, US', value: 'en-US'},
          {text: 'English, Welsh', value: 'en-WL'},
          // Disabled until 'fa' supported by AWS Translate
          // {text: 'Farsi', value: 'fa-IR'},
          {text: 'French', value: 'fr-FR'},
          {text: 'French, Canadian', value: 'fr-CA'},
          {text: 'German', value: 'de-DE'},
          {text: 'German, Swiss', value: 'de-CH'},
          {text: 'Hebrew', value: 'he-IL'},
          {text: 'Hindi', value: 'hi-IN'},
          {text: 'Indonesian', value: 'id-ID'},
          {text: 'Italian', value: 'it-IT'},
          {text: 'Japanese', value: 'ja-JP'},
          {text: 'Korean', value: 'ko-KR'},
          {text: 'Malay', value: 'ms-MY'},
          {text: 'Portuguese', value: 'pt-PT'},
          {text: 'Portuguese, Brazilian', value: 'pt-BR'},
          {text: 'Russian', value: 'ru-RU'},
          {text: 'Spanish', value: 'es-ES'},
          {text: 'Spanish, US', value: 'es-US'},
          {text: 'Tamil', value: 'ta-IN'},
          // Disabled until 'te' supported by AWS Translate
          // {text: 'Telugu', value: 'te-IN'},
          {text: 'Turkish', value: 'tr-TR'},
        ],
        translateLanguages: [
          {text: 'Afrikaans', value: 'af'},
          {text: 'Albanian', value: 'sq'},
          {text: 'Amharic', value: 'am'},
          {text: 'Arabic', value: 'ar'},
          {text: 'Azerbaijani', value: 'az'},
          {text: 'Bengali', value: 'bn'},
          {text: 'Bosnian', value: 'bs'},
          {text: 'Bulgarian', value: 'bg'},
          {text: 'Chinese (Simplified)', value: 'zh'},
          // AWS Translate does not support translating from zh to zh-TW
          // {text: 'Chinese (Traditional)', value: 'zh-TW'},
          {text: 'Croatian', value: 'hr'},
          {text: 'Czech', value: 'cs'},
          {text: 'Danish', value: 'da'},
          {text: 'Dari', value: 'fa-AF'},
          {text: 'Dutch', value: 'nl'},
          {text: 'English', value: 'en'},
          {text: 'Estonian', value: 'et'},
          {text: 'Finnish', value: 'fi'},
          {text: 'French', value: 'fr'},
          {text: 'French (Canadian)', value: 'fr-CA'},
          {text: 'Georgian', value: 'ka'},
          {text: 'German', value: 'de'},
          {text: 'Greek', value: 'el'},
          {text: 'Hausa', value: 'ha'},
          {text: 'Hebrew', value: 'he'},
          {text: 'Hindi', value: 'hi'},
          {text: 'Hungarian', value: 'hu'},
          {text: 'Indonesian', value: 'id'},
          {text: 'Italian', value: 'it'},
          {text: 'Japanese', value: 'ja'},
          {text: 'Korean', value: 'ko'},
          {text: 'Latvian', value: 'lv'},
          {text: 'Malay', value: 'ms'},
          {text: 'Norwegian', value: 'no'},
          {text: 'Persian', value: 'fa'},
          {text: 'Pashto', value: 'ps'},
          {text: 'Polish', value: 'pl'},
          {text: 'Portuguese', value: 'pt'},
          {text: 'Romanian', value: 'ro'},
          {text: 'Russian', value: 'ru'},
          {text: 'Serbian', value: 'sr'},
          {text: 'Slovak', value: 'sk'},
          {text: 'Slovenian', value: 'sl'},
          {text: 'Somali', value: 'so'},
          {text: 'Spanish', value: 'es'},
          {text: 'Swahili', value: 'sw'},
          {text: 'Swedish', value: 'sv'},
          {text: 'Tagalog', value: 'tl'},
          {text: 'Tamil', value: 'ta'},
          {text: 'Thai', value: 'th'},
          {text: 'Turkish', value: 'tr'},
          {text: 'Ukrainian', value: 'uk'},
          {text: 'Urdu', value: 'ur'},
          {text: 'Vietnamese', value: 'vi'},
        ],
        // translateLanguageTags is the same as translateLanguages except
        // with keys and values flipped around. We need this field ordering
        // for the voerro-tags-input. The flipping is done in mounted().
        translateLanguageTags: [],
        selectedTranslateLanguages: [],
        // TODO: get sourceLanguageCode from web form
        sourceLanguageCode: "en",
        targetLanguageCode: "es",
        uploadErrorMessage: "",
        invalidFileMessage: "",
        invalidFileMessages: [],
        showInvalidFile: false,
        dismissSecs: 8,
        dismissCountDown: 0,
        executed_assets: [],
        workflow_status_polling: null,
        description: "Click start to begin. Media analysis status will be shown after upload completes.",
        s3_destination: 's3://' + this.DATAPLANE_BUCKET,
        dropzoneOptions: {
          url: 'https://' + this.DATAPLANE_BUCKET + '.s3.amazonaws.com',
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
        let validStatus = true;
        if (this.invalid_file_types || this.textFormError || this.audioFormError || this.videoFormError) validStatus = false;
        return validStatus;
      },
      translateWorkflowConfig() {
        return {
          "Name": "TranscribeWorkflow",
          "Configuration": {

          }
        }
      },
      kitchenSinkWorkflowConfig() {
        return {
          "Name": "MieCompleteWorkflow2",
          "Configuration": {
            "defaultPrelimVideoStage2": {
              "Thumbnail": {
                "ThumbnailPosition": this.thumbnail_position.toString(),
                "MediaType": "Video",
                "Enabled": true
              },
              "Mediainfo": {"MediaType": "Video", "Enabled": true}
            },
            "MediaconvertStage2": {"Mediaconvert": {"MediaType": "Video", "Enabled": true}},
            "CaptionFileStage2": {
              "WebToSRTCaptions": {
                "MediaType": "MetadataOnly",
                "TargetLanguageCodes": Object.values(this.selectedTranslateLanguages.map(x => x.text)).concat(this.sourceLanguageCode),
                "Enabled": true
              },
              "WebToVTTCaptions": {
                "MediaType": "MetadataOnly",
                "TargetLanguageCodes": Object.values(this.selectedTranslateLanguages.map(x => x.text)).concat(this.sourceLanguageCode),
                "Enabled": true
              }
            },
            "WebCaptionsStage2": {
              "WebCaptions": {
                "MediaType": "Text",
                "SourceLanguageCode": this.sourceLanguageCode,
                "Enabled": true
              }
            },
            "TranslateStage2": {
              "Translate": {
                "MediaType":"Text",
                "Enabled": true,
                // TODO: get these values from webform
                "TargetLanguageCode":"ru",
                "SourceLanguageCode":"en"
              },
              "TranslateWebCaptions": {
                "MediaType":"Text",
                "Enabled":true,
                "TargetLanguageCodes": Object.values(this.selectedTranslateLanguages.map(x => x.text)),
                "SourceLanguageCode": this.sourceLanguageCode
              }
            },
            "defaultAudioStage2": {
              "Transcribe": {
                "MediaType": "Audio",
                "Enabled": this.enabledOperators.includes("Transcribe"),
                // TODO: get transcribe language from webform
                "TranscribeLanguage": "en-US"
              }
            },
            "defaultTextSynthesisStage2": {"Polly": {"MediaType": "Text", "Enabled": false}},
            "defaultVideoStage2": {
              "faceDetection": {"MediaType": "Video", "Enabled": this.enabledOperators.includes("faceDetection")},
              "textDetection": {"MediaType": "Video", "Enabled": this.enabledOperators.includes("textDetection")},
              "celebrityRecognition": {"MediaType": "Video", "Enabled": this.enabledOperators.includes("celebrityRecognition")},
              "GenericDataLookup": {"MediaType": "Video", "Enabled": false},
              "labelDetection": {"MediaType": "Video", "Enabled": this.enabledOperators.includes("labelDetection")},
              "personTracking": {"MediaType": "Video", "Enabled": false},
              "Mediaconvert": {"MediaType": "Video", "Enabled": false},
              "contentModeration": {"MediaType": "Video", "Enabled": this.enabledOperators.includes("contentModeration")},
              "faceSearch": {
                "MediaType": "Video",
                "Enabled": this.enabledOperators.includes("faceSearch"),
                "CollectionId": this.faceCollectionId==="" ? "undefined" : this.faceCollectionId
              }
            },
            "defaultTextStage2": {
              "ComprehendEntities": {"MediaType": "Text", "Enabled": true},
              "ComprehendKeyPhrases": {"MediaType": "Text", "Enabled": true}
            }
          }
        }
      }
    },
    mounted: function() {
      this.translateLanguageTags=this.translateLanguages.map(x => {return {"text": x.value, "value": x.text}})
      this.executed_assets = this.execution_history;
      this.pollWorkflowStatus();
      // TODO: make sure the source language is not a target translate language
      // this.selectedTranslateLanguages = this.selectedTranslateLanguages.map(x => x.value).filter(x => x.value!=this.sourceLanguageCode);
    },
    beforeDestroy () {
      clearInterval(this.workflow_status_polling)
    },
    methods: {
      selectAll: function (){
        this.enabledOperators = ['labelDetection', 'celebrityRecognition', 'textDetection', 'contentModeration', 'faceDetection', 'thumbnail', 'Transcribe', 'Translate', 'ComprehendKeyPhrases', 'ComprehendEntities'];
        this.show_disclaimer = true;
        this.create_video_stream = true;

      },
      clearAll: function (){
        this.enabledOperators = [];
        this.show_disclaimer = false;
        this.create_video_stream = false;
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
      fileAdded: function( file )
      {
        let errorMessage = '';
        if (!(file.type).match(/image\/.+|video\/.+|application\/json/g) && !this.valid_media_types.includes(file.name.split('.').pop().toLowerCase())) {
          if (file.type === "") {
            console.log("here")
            errorMessage = "Unsupported file type: unknown";
          }
          else
            errorMessage = "Unsupported file type: " + file.type;
          this.invalidFileMessages.push(errorMessage);
          this.showInvalidFile = true
        }
      },
      fileRemoved: function( file )
      {
        let errorMessage = '';
        if (!(file.type).match(/image\/.+|video\/.+|application\/json/g)) {
          if (file.type === "")
            errorMessage = "Unsupported file type: unknown";
          else
            errorMessage = "Unsupported file type: " + file.type;
        }
        this.invalidFileMessages = this.invalidFileMessages.filter(function(value){ return value != errorMessage})
        if (this.invalidFileMessages.length === 0 ) this.showInvalidFile = false;
      },
      s3UploadComplete: async function (location) {
        const token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
        const vm = this;
        const s3_uri = location.s3ObjectLocation.url + location.s3ObjectLocation.fields.key;
        const media_type = location.type;
        console.log('media type: ' + media_type);
        console.log('s3UploadComplete: ');
        console.log(s3_uri);
        let data = {};
        if (media_type.match(/image/g)) {
          data = {
            "Name": "ImageWorkflow",
            "Configuration": {
              "ValidationStage": {
                "MediainfoImage": {
                  "Enabled": true
                }
              },
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
                  "S3Bucket": this.DATAPLANE_BUCKET,
                  "S3Key": location.s3ObjectLocation.fields.key
                }
              }
            }
          };
        } else if (media_type.match(/video/g) || this.valid_media_types.includes(location.s3ObjectLocation.fields.key.split('.').pop().toLowerCase())) {
          data = vm.kitchenSinkWorkflowConfig;
          // data = vm.translateWorkflowConfig;
          data["Input"] = {
            "Media": {
              "Video": {
                "S3Bucket": this.DATAPLANE_BUCKET,
                "S3Key": location.s3ObjectLocation.fields.key
              }
            }
          };
        } else if (media_type === 'application/json') {
          // JSON files may be uploaded for the genericDataLookup operator, but
          // we won't run a workflow for json file types.
          console.log("Data file has been uploaded to s3://" + location.s3ObjectLocation.fields.key);
          return;
        } else {
          vm.s3UploadError("Unsupported media type: " + media_type + ".")
        }
        console.log(JSON.stringify(data));
        fetch(this.WORKFLOW_API_ENDPOINT + 'workflow/execution', {
          method: 'post',
          body: JSON.stringify(data),
          headers: {'Content-Type': 'application/json', 'Authorization': token}
        }).then(response =>
          response.json().then(data => ({
              data: data,
              status: response.status
            })
          ).then(res => {
            if (res.status !== 200) {
              console.log("ERROR: Failed to start workflow.");
              console.log(res.data.Code);
              console.log(res.data.Message);
              console.log("URL: " + this.WORKFLOW_API_ENDPOINT + 'workflow/execution');
              console.log("Data:");
              console.log(JSON.stringify(data));
              console.log((data));
              console.log("Response: " + response.status);
            } else {
              const asset_id = res.data.AssetId;
              const s3key = location.s3ObjectLocation.fields.key;
              console.log("Media assigned asset id: " + asset_id);
              vm.executed_assets.push({asset_id: asset_id, file_name: s3key, workflow_status: "", state_machine_console_link: ""});
              vm.getWorkflowStatus(asset_id);
            }
          })
        )
      },
      async getWorkflowStatus(asset_id) {
        const token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
        const vm = this;
        fetch(this.WORKFLOW_API_ENDPOINT+'workflow/execution/asset/'+asset_id, {
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
            if (res.status !== 200) {
              console.log("ERROR: Failed to get workflow status")
            } else {
              for (let i = 0; i < vm.executed_assets.length; i++) {
                if (vm.executed_assets[i].asset_id === asset_id) {
                  vm.executed_assets[i].workflow_status = res.data[0].Status;
                  vm.executed_assets[i].state_machine_console_link = "https://"+this.AWS_REGION+".console.aws.amazon.com/states/home?region="+this.AWS_REGION+"#/executions/details/"+res.data[0].StateMachineExecutionArn;
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
        const poll_frequency = 5000;
        this.workflow_status_polling = setInterval(() => {
          this.executed_assets.forEach(item => {
            if (item.workflow_status === "" || item.workflow_status === "Started" || item.workflow_status === "Queued") {
              this.getWorkflowStatus(item.asset_id)
            }
          });
        }, poll_frequency)
      },
      uploadFiles() {
        console.log("Uploading to s3://" + this.DATAPLANE_BUCKET,);
        const signurl = this.DATAPLANE_API_ENDPOINT + '/upload';
        this.$refs.myVueDropzone.setAWSSigningURL(signurl);
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
