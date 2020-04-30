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
          <b-form-input :disabled="workflow_status !== 'Complete'" class="compact-height start-time-field " :value="data.item.start" @change="new_time => changeStartTime(new_time, data.index)"/>
          <b-form-input :disabled="workflow_status !== 'Complete'" class="compact-height stop-time-field " :value="data.item.end" @change="new_time => changeEndTime(new_time, data.index)"/>
        </template>
        <template v-slot:cell(caption)="data">
          <b-container class="p-0">
            <b-row no-gutters>
              <b-col cols="10">
          <b-form-textarea :disabled="workflow_status !== 'Complete'" :ref="'caption' + data.index" class="custom-text-field .form-control-sm" max-rows="8" :value="data.item.caption" placeholder="Type subtitle here" @change="new_caption => changeCaption(new_caption, data.index)" @click='captionClickHandler(data.index)'/>
              </b-col>
              <b-col>
                <span style="position:absolute; top: 0px">
                  <b-button v-if="workflow_status === 'Complete'" size="sm" variant="link" @click="delete_row(data.index)">
                    <b-icon icon="x-circle" color="lightgrey"></b-icon>
                  </b-button>
                </span>
                <span style="position:absolute; bottom: 0px">
                  <b-button v-if="workflow_status === 'Complete'" size="sm" variant="link" @click="add_row(data.index)">
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
<!-- Uncomment to enable Upload button -->
<!--      <b-button id="showModal" size="sm" class="mb-2" @click="showModal()">-->
<!--        <b-icon icon="upload" color="white"></b-icon> Upload JSON-->
<!--      </b-button> &nbsp;-->
      <b-button id="downloadCaptionsVTT" size="sm" class="mb-2" @click="downloadCaptionsVTT()">
        <b-icon v-if="this.webCaptions.length > 0" icon="download" color="white"></b-icon> Download VTT
      </b-button> &nbsp;
      <b-button v-if="this.workflow_status === 'Waiting'" id="saveCaptions" size="sm" class="mb-2" @click="saveCaptions()">
        <b-icon v-if="this.isSaving" icon="arrow-clockwise" animation="spin"  color="white"></b-icon>
        <b-icon v-else icon="play" color="white"></b-icon>
        Save changes
      </b-button>
      <b-button v-if="this.workflow_status === 'Complete' || this.workflow_status === 'Error'" id="editCaptions" size="sm" class="mb-2" @click="showSaveConfirmation()">
        <b-icon icon="play" color="white"></b-icon>
        Save captions
      </b-button>
      <b-button v-if="this.workflow_status === 'Started'" id="editCaptionsDisabled" size="sm" disabled class="mb-2" @click="saveCaptions()">
        <b-icon icon="arrow-clockwise" animation="spin"  color="white"></b-icon>
        Save captions
      </b-button>
      <b-modal ref="save-modal" title="Save Confirmation" @ok="saveCaptions()" ok-title="Confirm">
        <p>Saving captions will restart a workflow that can take several minutes. You will not be able to edit captions until it has finished. Are you ready to proceed?</p>
      </b-modal>

<!-- Uncomment to enable Upload button -->
<!--      <b-modal ref="my-modal" hide-footer title="Upload a file">-->
<!--        <p>Upload a timed subtitles file in the Webcaptions JSON format.</p>-->
<!--        <div>-->
<!--          <input type="file" @change="uploadCaptionsFile">-->
<!--        </div>-->
<!--      </b-modal>-->
      <div style="color:red" v-if="this.webCaptions.length > 0 && this.workflow_status !== 'Complete' && this.workflow_status !== 'Error' && this.workflow_status !== 'Waiting'">
        Caption editing is disabled until workflow completes.
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: "Transcript",
  data() {
    return {
      asset_id: this.$route.params.asset_id,
      workflow_id: "",
      workflow_status: "",
      waiting_stage: "",
      sourceLanguageCode: "",
      workflow_config: {},
      showSaveNotification: 0,
      saveNotificationMessage: "Captions saved",
      results: [],
      webCaptions: [],
      webCaptions_vtt: '',
      webCaptions_fields: [
        {key: 'timeslot', label: 'timeslot', tdClass: this.tdClassFunc},
        {key: 'caption', label: 'caption'}
        ],
      uploaded_captions_file: '',
      id: 0,
      transcript: "",
      isBusy: false,
      isSaving: false,
      operator: "transcript",
      noTranscript: false
    }
  },
  computed: {
    inputListeners: function () {
      var vm = this
      // `Object.assign` merges objects together to form a new object
      return Object.assign({},
        // We add all the listeners from the parent
        this.$listeners,
        // Then we can add custom listeners or override the
        // behavior of some listeners.
        {
          // This ensures that the component works with v-model
          input: function (event) {
            vm.$emit('input', event.target.value)
          }
        }
      )
    },
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
    this.isBusy = true;
    this.getTimeUpdate();
    this.getWorkflowId();
    this.pollWorkflowStatus();
    // uncomment this whenever we need to get data from Elasticsearch
    // this.fetchAssetData();
  },
  beforeDestroy: function () {
      this.transcript = ''
  },
  methods: {
    sortWebCaptions(item) {
      console.log("sorting captions")
      // Keep the webCaptions table sorted on caption start time
      this.webCaptions.sort((a,b) => {
        a=parseFloat(a["start"])
        b=parseFloat(b["start"])
        return a<b?-1:1
      });
      if (item) {
        // Since table has mutated, regain focus on the row that the user is editing
        const new_index = this.webCaptions.findIndex(element => {
          return (element.start === item.start)
        })
        this.$refs["caption" + (new_index)].focus();
      }
    },
    changeStartTime(new_time, index) {
      this.webCaptions[index].start = new_time
      this.sortWebCaptions(this.webCaptions[index])
    },
    changeEndTime(new_time, index) {
      this.webCaptions[index].end = new_time
    },
    changeCaption(new_caption, index) {
      this.webCaptions[index].caption = new_caption
    },
    captionClickHandler(index) {
      // pause video player and jump to the time for the selected caption
      this.player.currentTime(this.webCaptions[index].start)
      this.player.pause()
    },
    // Format a VTT timestamp in HH:MM:SS.mmm
    formatTimeVTT(timeSeconds) {
      const ONE_HOUR = 60 * 60
      const ONE_MINUTE = 60
      const hours = Math.floor(timeSeconds / ONE_HOUR)
      let remainder = timeSeconds - (hours * ONE_HOUR)
      const minutes = Math.floor(remainder / 60)
      remainder = remainder - (minutes * ONE_MINUTE)
      const seconds = Math.floor(remainder)
      remainder = remainder - seconds
      const millis = remainder

      return hours.toString().padStart(2, '0') + ':' + minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0') + '.' + Math.floor(millis * 1000).toString().padStart(3, '0')
    },
    webToVtt()
    {
      let vtt = 'WEBVTT\n\n'
      for (let i = 0; i < this.webCaptions.length; i++) {
        const caption = this.webCaptions[i]
        vtt += this.formatTimeVTT(caption["start"]) + ' --> ' + this.formatTimeVTT(caption["end"]) + '\n';
        vtt += caption["caption"] + '\n\n';
      }
      this.webCaptions_vtt = vtt;
    },
    getTimeUpdate() {
      // Send current time position for the video player to verticalLineCanvas
      var last_position = 0;
      if (this.player) {
        this.player.on('timeupdate', function () {
          const current_position = Math.round(this.player.currentTime());
          if (current_position !== last_position) {
            let timeline_position = this.webCaptions.findIndex(function(item, i){return (parseInt(item.start) <= current_position && parseInt(item.end) >= current_position)})
            if (this.$refs.selectableTable) {
              this.$refs.selectableTable.selectRow(timeline_position)
            }
            last_position = current_position;
          }
        }.bind(this));
      }
    },
    getWorkflowId: async function() {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      fetch(this.WORKFLOW_API_ENDPOINT + '/workflow/execution/asset/' + this.asset_id, {
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
              this.getTranscribeLanguage(token)
              // get workflow config, needed for edit captions button
              this.getWorkflowConfig(token);
            }
          )
        }
      )
    },
    getWorkflowStatus: async function() {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      fetch(this.WORKFLOW_API_ENDPOINT + '/workflow/execution/asset/' + this.asset_id, {
        method: 'get',
        headers: {
          'Authorization': token
        }
      }).then(response => {
          response.json().then(data => ({
              data: data,
            })
          ).then(res => {
              this.workflow_status = res.data[0].Status
            }
          )
        }
      )
    },
    getTranscribeLanguage: async function(token) {
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
    getWorkflowConfig: async function(token) {
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
            this.workflow_config = res.data.Configuration
          })
        }
      )
    },
    resumeWorkflow: async function() {
      // This function executes a paused workflow from the WaitingStageName stage.
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
    rerunWorkflow: async function (token) {
      // This function reruns all the operators downstream from transcribe.
      let data = {
        "Name": "MieCompleteWorkflow2",
        "Configuration": this.workflow_config
      }
      data["Input"] = {
        "AssetId": this.asset_id
      };
      // execute the workflow
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
            this.saveNotificationMessage += " and workflow resumed"
            console.log("workflow executing");
            console.log(res);
          }
        })
      )
    },
    saveCaptions: async function (token) {
      // This function saves captions to the dataplane
      // and reruns or resumes the workflow.
      this.$refs['save-modal'].hide()
      this.isSaving=true;
      if (!token) {
        token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
      }
      const operator_name = "WebCaptions_"+this.sourceLanguageCode
      const webCaptions = {"WebCaptions": this.webCaptions}
      let data='{"OperatorName": "' + operator_name + '", "Results": ' + JSON.stringify(webCaptions) + ', "WorkflowId": "' + this.workflow_id + '"}'
      fetch(this.DATAPLANE_API_ENDPOINT + 'metadata/' + this.asset_id, {
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
            this.isSaving=true;
            console.log("Captions saved")
            this.saveNotificationMessage = "Captions saved"
            if (this.workflow_status === "Waiting") {
              this.resumeWorkflow();
              this.workflow_status = "Started";
            } else if (this.workflow_status === "Complete" ||
              this.workflow_status === "Error") {
              this.rerunWorkflow(token);
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
    downloadCaptionsVTT() {
      this.webToVtt()
      const data = JSON.stringify(this.webCaptions_vtt);
      const blob = new Blob([data], {type: 'text/plain'});
      const e = document.createEvent('MouseEvents'),
        a = document.createElement('a');
      a.download = "WebCaptions.vtt";
      a.href = window.URL.createObjectURL(blob);
      a.dataset.downloadurl = ['text/json', a.download, a.href].join(':');
      e.initEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
      a.dispatchEvent(e);
    },
    // Uncomment to enable Upload button
    // showModal() {
    //   this.$refs['my-modal'].show()
    // },
    showSaveConfirmation() {
      this.$refs['save-modal'].show()
    },
    uploadCaptionsFile(event) {
      // Uncomment to enable Upload button
      // this.$refs['my-modal'].hide()
      const file = event.target.files[0];
      const reader = new FileReader();
      reader.onload = e => this.webCaptions = JSON.parse(e.target.result);
      reader.readAsText(file);
      this.sortWebCaptions();
    },
    getWebCaptions: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      // TODO: Get workflow id so you can get the workflow configuration
      // TODO: Get source language from workflow configuration
      // Get paginated web captions
      const operator_name = "WebCaptions_"+this.sourceLanguageCode
      let cursor=''
      let url = this.DATAPLANE_API_ENDPOINT + '/metadata/' + this.asset_id + '/' + operator_name
      this.webCaptions = []
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
            this.webCaptions = res.data.results["WebCaptions"]
            this.sortWebCaptions()
            this.isBusy = false
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
      this.player.currentTime(this.webCaptions[index+1].start)
      this.player.pause()
    },
    delete_row(index) {
      this.webCaptions.splice(index, 1)
    },
    async fetchAssetData () {
      let query = 'AssetId:'+this.asset_id+ ' _index:mietranscript';
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
    },
    pollWorkflowStatus() {
      // Poll frequency in milliseconds
      const poll_frequency = 5000;
      this.workflow_status_polling = setInterval(() => {
        this.getWorkflowStatus();
      }, poll_frequency)
    },
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
    background-color: white !important;
  }
  .stop-time-field {
    padding: 0 !important;
    margin: 0 !important;
    border: 0 !important;
    height: auto;
    background-color: white !important;
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
    background-color: white !important;
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
  .scroller {
    height: 100vh;
  }
  .vue-recycle-scroller__slot,
  .vue-recycle-scroller__item-view {
    display: flex;
    width: 100%;
  }
  .th,
  .td {
    flex: 1;
  }
  .vue-recycle-scroller__slot .th:first-child,
  .vue-recycle-scroller__item-view .td:first-child {
    flex: 2;
  }
</style>
