<template>
  <div>
    <div v-if="noTranscript === true">
      No transcript found for this asset
    </div>
    <b-alert
        v-model="showSaveNotification"
        variant="success"
        dismissible
        fade
    >
      {{ saveNotificationMessage }}
    </b-alert>
    <div v-if="isBusy">
      <b-spinner
        variant="secondary"
        label="Loading..."
      />
      <p class="text-muted">
        (Loading...)
      </p>
    </div>
    <div v-else>
      <div v-if="isProfane">
        <span style="color:red">WARNING: Transcript contains potentially offensive words.</span>
        <br>
        <br>
      </div>
      <div id="event-line-editor" class="event-line-editor">
      <b-table
          selectable
          select-mode="single"
          thead-class="hidden_header"
          fixed responsive="sm"
          :items="webCaptions"
          :fields="webCaptions_fields" ref="selectableTable"
      >
        <!-- adjust column width for captions -->
        <template v-slot:table-colgroup="scope">
          <col
              v-for="field in scope.fields"
              :key="field.key"
              :style="{ width: field.key === 'caption' ? '80%' : '20%' }"
          >
        </template>
        <template v-slot:cell(timeslot)="data">
          <b-form-input class="compact-height start-time-field " v-model="data.item.start"/>
          <b-form-input class="compact-height stop-time-field " v-model="data.item.end"/>
        </template>
        <template v-slot:cell(caption)="data">
          <b-container class="p-0">
            <b-row no-gutters>
              <b-col cols="10">
          <b-form-textarea :ref="'caption' + data.index" class="custom-text-field .form-control-sm" max-rows="8" v-model="data.item.caption" placeholder="Type subtitle here"/>
              </b-col>
              <b-col>
                <span style="position:absolute; top: 0px">
                  <b-button size="sm" variant="link" @click="delete_row(data.index)">
                    <b-icon icon="x-circle" color="lightgrey"></b-icon>
                  </b-button>
                </span>
                <span style="position:absolute; bottom: 0px">
                  <b-button size="sm" variant="link" @click="add_row(data.index)">
                    <b-icon icon="plus-square" color="lightgrey"></b-icon>
                  </b-button>
                </span>
              </b-col>
            </b-row>
          </b-container>
        </template>
      </b-table>
      </div>
    </div>
    <div><br>
      <b-button id="showModal" size="sm" class="mb-2" @click="showModal()">
        <b-icon icon="upload" color="white"></b-icon> Upload
      </b-button> &nbsp;
      <b-button id="downloadCaptions" size="sm" class="mb-2" @click="downloadCaptions()">
        <b-icon icon="download" color="white"></b-icon> Download
      </b-button> &nbsp;
      <b-button id="saveCaptions" size="sm" class="mb-2" @click="saveCaptions()">
        <b-icon icon="play" color="white"></b-icon> Save changes
      </b-button>

      <b-modal ref="my-modal" hide-footer title="Upload a file">
        <p>Upload a timed subtitles file in the Webcaptions JSON format.</p>
        <div>
          <input type="file" @change="uploadCaptionsFile">
        </div>
      </b-modal>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: "Transcript",
  data() {
    return {
      workflow_id: "",
      workflow_status: "",
      waiting_stage: "",
      sourceLanguageCode: "",
      showSaveNotification: 0,
      saveNotificationMessage: "Captions saved",
      results: [],
      webCaptions: [],
      webCaptions_fields: [
        {key: 'timeslot', label: 'timeslot', tdClass: this.tdClassFunc},
        {key: 'caption', label: 'caption'}
        ],
      uploaded_captions_file: '',
      id: 0,
      transcript: "",
      isBusy: false,
      operator: "transcript",
      noTranscript: false
    }
  },
  computed: {
    ...mapState(['player']),
    isProfane() {
      const Filter = require('bad-words');
      const profanityFilter = new Filter({ placeHolder: '_' });
      return profanityFilter.isProfane(this.transcript);
    },
  },
  deactivated: function () {
    console.log('deactivated component:', this.operator)
  },
  activated: function () {
    console.log('activated component:', this.operator);
    this.getTimeUpdate();
    this.getWorkflowId();
    // uncomment this whenever we need to get data from Elasticsearch
    // this.fetchAssetData();
  },
  beforeDestroy: function () {
      this.transcript = ''
  },
  methods: {
    getTimeUpdate() {
      // Send current time position for the video player to verticalLineCanvas
      var last_position = 0;
      if (this.player) {
        this.player.on('timeupdate', function () {
          const current_position = Math.round(this.player.currentTime());
          if (current_position !== last_position) {
            let timeline_position = this.webCaptions.findIndex(function(item, i){return (parseInt(item.start) <= current_position && parseInt(item.end) >= current_position)})
            this.$refs.selectableTable.selectRow(timeline_position)
            last_position = current_position;
          }
        }.bind(this));
      }
    },
    getWorkflowId: async function() {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const asset_id = this.$route.params.asset_id;
      fetch(this.WORKFLOW_API_ENDPOINT + '/workflow/execution/asset/' + asset_id, {
        method: 'get',
        headers: {
          'Authorization': token
        }
      }).then(response => {
          response.json().then(data => ({
              data: data,
            })
          ).then(res => {
              this.workflow_id = res.data[0].Id
              this.workflow_status = res.data[0].Status
              if ("CurrentStage" in res.data[0])
                this.waiting_stage = res.data[0].CurrentStage
              this.getTranscribeLanguage()
            }
          )
        }
      )
    },
    getTranscribeLanguage: async function() {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const asset_id = this.$route.params.asset_id;
      fetch(this.WORKFLOW_API_ENDPOINT + '/workflow/execution/' + this.workflow_id, {
        method: 'get',
        headers: {
          'Authorization': token
        }
      }).then(response => {
          response.json().then(data => ({
              data: data,
            })
          ).then(res => {
              this.sourceLanguageCode = res.data.Configuration.WebCaptionsStage2.WebCaptions.SourceLanguageCode
              this.getWebCaptions()
            }
          )
        }
      )
    },
    resumeWorkflow: async function() {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const data = JSON.stringify({"WaitingStageName": this.waiting_stage});
      fetch(this.WORKFLOW_API_ENDPOINT + 'workflow/execution/' + this.workflow_id, {
        method: 'put',
        body: data,
        headers: {'Content-Type': 'application/json', 'Authorization': token}
      }).then(response =>
        response.json().then(data => ({
            data: data,
            status: response.status
          })
        ).then(res => {
          if (res.status === 200) {
            console.log("Workflow resumed")
            this.saveNotificationMessage += " and workflow resumed"
          }
        })
      )
    },
    saveCaptions: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const operator_name = "WebCaptions_"+this.sourceLanguageCode
      const asset_id = this.$route.params.asset_id;
      let data='{"OperatorName": "' + operator_name + '", "Results": ' + JSON.stringify(this.webCaptions) + ', "WorkflowId": "' + this.workflow_id + '"}'
      // save caption data to workflow metadata
      fetch(this.DATAPLANE_API_ENDPOINT + 'metadata/' + asset_id, {
        method: 'post',
        body: data,
        headers: {'Content-Type': 'application/json', 'Authorization': token}
      }).then(response =>
        response.json().then(data => ({
            data: data,
            status: response.status
          })
        ).then(res => {
          if (res.status === 200) {
            console.log("Captions saved")
            this.saveNotificationMessage = "Captions saved"
            if (this.workflow_status === "Waiting") {
              this.resumeWorkflow()
            }
            this.showSaveNotification = 5;
          }
          if (res.status !== 200) {
            console.log("ERROR: Failed to upload captions.");
            console.log(res.data.Code);
            console.log(res.data.Message);
            console.log("Response: " + response.status);
          }
        })
      )
    },
    downloadCaptions() {
      const data = JSON.stringify(this.webCaptions);
      const blob = new Blob([data], {type: 'text/plain'});
      const e = document.createEvent('MouseEvents'),
        a = document.createElement('a');
      a.download = "WebCaptions.json";
      a.href = window.URL.createObjectURL(blob);
      a.dataset.downloadurl = ['text/json', a.download, a.href].join(':');
      e.initEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
      a.dispatchEvent(e);
    },
    showModal() {
      this.$refs['my-modal'].show()
    },
    uploadCaptionsFile(event) {
      this.$refs['my-modal'].hide()
      const file = event.target.files[0];
      const reader = new FileReader();
      reader.onload = e => this.webCaptions = JSON.parse(e.target.result);
      reader.readAsText(file);
    },
    getWebCaptions: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      // TODO: Get workflow id so you can get the workflow configuration
      // TODO: Get source language from workflow configuration
      // Get paginated web captions
      const asset_id = this.$route.params.asset_id;
      const operator_name = "WebCaptions_"+this.sourceLanguageCode
      let cursor=''
      let url = this.DATAPLANE_API_ENDPOINT + '/metadata/' + asset_id + '/' + operator_name
      this.getWebCaptionPages(token, url, cursor)
    },
    getWebCaptionPages: async function (token, url, cursor) {
      fetch((cursor.length === 0) ? url : url + '?cursor=' + cursor, {
        method: 'get',
        headers: {
          'Authorization': token
        },
      }).then(response => {
        response.json().then(data => ({
            data: data,
            status: response.status
          })
        ).then(res => {
          if (res.status !== 200) {
            console.log("ERROR: Failed to upload captions.");
            console.log(res.data.Code);
            console.log(res.data.Message);
            console.log("Response: " + res.status);
          }
          if (res.data.results) {
            cursor = res.data.cursor;
            this.webCaptions.push(res.data.results)
            if (cursor)
              this.getWebCaptionPages(token,url,cursor)
          } else {
            this.videoOptions.captions = []
          }
        })
      });
    },
    add_row(index) {
      this.webCaptions.splice(index+1, 0, {"start":this.webCaptions[index].end,"caption":"","end":this.webCaptions[index+1].start})
      this.$refs["caption"+(index+1)].focus();
    },
    delete_row(index) {
      this.webCaptions.splice(index, 1)
    },
    async fetchAssetData () {
      let query = 'AssetId:'+this.$route.params.asset_id+ ' _index:mietranscript';
      let apiName = 'mieElasticsearch';
      let path = '/_search';
      let apiParams = {
        headers: {'Content-Type': 'application/json'},
        queryStringParameters: {'q': query, 'default_operator': 'AND', 'size': 10000}
      };
      let response = await this.$Amplify.API.get(apiName, path, apiParams);
      if (!response) {
        this.showElasticSearchAlert = true
      }
      else {
        let result = await response;
        let data = result.hits.hits;
        if (data.length === 0) {
          this.noTranscript = true
        }
        else {
          this.noTranscript = false;
          for (let i = 0, len = data.length; i < len; i++) {
            this.transcript = data[i]._source.transcript
          }
        }
        this.isBusy = false
      }
    }
  },
}
</script>

<style>
  .start-time-field {
    padding: 0 !important;
    margin: 0 !important;
    margin-bottom: 4px !important;
    border: 0 !important;
    height: auto;
  }
  .stop-time-field {
    padding: 0 !important;
    margin: 0 !important;
    border: 0 !important;
    height: auto;
  }
  .hidden_header {
    display: none;
  }
  .event-line-editor {
    overflow: scroll;
    height: 500px;
    border-top: 1px solid #e2e2e2;
    border-bottom: 1px solid #e2e2e2;
  }
  /* these options needed for MacOS to make scrollbar visible when not in use */
  .event-line-editor::-webkit-scrollbar {
    -webkit-appearance: none;
    width: 7px;
  }
  /* these options needed for MacOS to make scrollbar visible when not in use */
  .event-line-editor::-webkit-scrollbar-thumb {
    border-radius: 4px;
    background-color: rgba(0, 0, 0, .5);
    -webkit-box-shadow: 0 0 1px rgba(255, 255, 255, .5);
  }
  .custom-text-field {
    border: 0;
  }
  .highlightedBorder {
    border-left: 1px solid #cc181e;
    background-color: green;
  }
  tr.b-table-row-selected {
    border-left: 1px solid #cc181e !important;
  }
  table.b-table-selectable > tbody > tr.b-table-row-selected > td {
    background-color: white !important;
  }
</style>
