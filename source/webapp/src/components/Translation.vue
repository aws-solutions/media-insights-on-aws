<template>
  <div>
    <div v-if="noTranslation === true">
      No translation found for this asset
    </div>
    <div
      v-if="isBusy"
      class="wrapper"
    >
      <b-spinner
        variant="secondary"
        label="Loading..."
      />
      <p class="text-muted">
        (Loading...)
      </p>
    </div>
    <div
      v-else-if="noTranslation === false"
      class="wrapper"
    >
      <b-form-group>
        <b-form-radio-group
            v-model="selected_lang_code"
            :options="alphabetized_language_collection"
            @change="getWebCaptions"
        ></b-form-radio-group>
      </b-form-group>
      <div v-if="selected_lang_code !== ''">
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
            <b-form-input :disabled="workflow_status !== 'Complete'" class="compact-height start-time-field " :value="toHHMMSS(data.item.start)" @change="new_time => changeStartTime(new_time, data.index)"/>
            <b-form-input :disabled="workflow_status !== 'Complete'" class="compact-height stop-time-field " :value="toHHMMSS(data.item.end)" @change="new_time => changeEndTime(new_time, data.index)"/>
          </template>
          <template v-slot:cell(caption)="data">
            <b-container class="p-0">
              <b-row no-gutters>
                <b-col cols="10">
                  <b-form-textarea :disabled="workflow_status !== 'Complete'" :id="'caption' + data.index" :ref="'caption' + data.index" class="custom-text-field .form-control-sm" rows="2" :value="data.item.caption" placeholder="Type subtitle here" @change="new_caption => changeCaption(new_caption, data.index)" @click='captionClickHandler(data.index)'/>
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
        <a :href="vtt_url">
          <b-button type="button" size="sm" class="mb-2">
            <b-icon v-if="this.webCaptions.length > 0" icon="download" color="white"></b-icon> Download VTT
          </b-button>
        </a> &nbsp;
        <a :href="srt_url">
          <b-button type="button" size="sm" class="mb-2">
            <b-icon v-if="this.webCaptions.length > 0" icon="download" color="white"></b-icon> Download SRT
          </b-button>
        </a>
      </div>
    </div>
  </div>
</template>

<script>
import {mapState} from "vuex";

export default {
  name: "Translation",
  data() {
    return {
      vttcaptions: [
        {
          src: "",
          lang: "",
          label: ""
        }
      ],
      srtcaptions: [
        {
          src: "",
          lang: "",
          label: ""
        }
      ],
      isBusy: false,
      operator: "translation",
      noTranslation: false,
      num_translations: 0,
      translationsCollection: [
      ],
      selected_lang: "",
      selected_lang_code: "",
      translatedText: "",
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
      asset_id: this.$route.params.asset_id,
      workflow_id: "",
      workflow_status: "",
      waiting_stage: "",
      sourceLanguageCode: "",
      workflow_config: {},
      workflow_definition: {},
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
      isSaving: false,
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
    ...mapState(['player', 'waveform_seek_position']),
    alphabetized_language_collection: function() {
      return this.translationsCollection.sort(function(a, b) {
        var textA = a.text.toUpperCase();
        var textB = b.text.toUpperCase();
        return (textA < textB) ? -1 : (textA > textB) ? 1 : 0;
      });
    },
    vtt_url: function() {
      if (this.selected_lang_code !== '') {
        let vttcaption = this.vttcaptions.filter(x => (x.lang === this.selected_lang_code))[0];
        if (vttcaption) {
          return vttcaption.src
        }
      }
    },
    srt_url: function() {
      if (this.selected_lang_code !== '') {
        let srtcaption = this.srtcaptions.filter(x => (x.lang === this.selected_lang_code))[0];
        if (srtcaption) {
          return srtcaption.src
        }
      }
    },
  },
  watch: {
    // When user moves the cursor on the waveform
    // then focus the corresponding row in the caption table.
    waveform_seek_position: function () {
      this.handleWaveformSeek();
    },
  },
  deactivated: function () {
    console.log('deactivated component:', this.operator)
  },
  activated: function () {
    console.log('activated component:', this.operator);
    this.getVttCaptions();
    this.getSrtCaptions();
    this.isBusy = true;
    this.handleVideoPlay();
    this.handleVideoSeek();
    this.getWorkflowId();
    this.pollWorkflowStatus();
  },
  beforeDestroy: function () {
    },
  methods: {
    getTxtTranslations: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      this.translationsCollection = [];
      const asset_id = this.$route.params.asset_id;
      fetch(this.DATAPLANE_API_ENDPOINT + '/metadata/' + asset_id + '/TranslateWebCaptions', {
        method: 'get',
        headers: {
          'Authorization': token
        }
      }).then(response => {
        response.json().then(data => ({
            data: data,
          })
        ).then(res => {
          this.num_translations = res.data.results.CaptionsCollection.length;
          res.data.results.CaptionsCollection.forEach(item => {
            const bucket = item.TranslationText.S3Bucket;
            const key = item.TranslationText.S3Key;
            // get URL to captions file in S3
            fetch(this.DATAPLANE_API_ENDPOINT + '/download', {
              method: 'POST',
              mode: 'cors',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': token
              },
              body: JSON.stringify({"S3Bucket": bucket, "S3Key": key})
            }).then(data => {
              data.text().then((data) => {
                let languageLabel = this.translateLanguages.filter(x => (x.value === item.TargetLanguageCode))[0].text;
                this.translationsCollection.push(
                  {text: languageLabel, value: item.TargetLanguageCode}
                );
                // set default language selection
                this.selected_lang_code = this.alphabetized_language_collection[0].value
                this.getWebCaptions()
              }).catch(err => console.error(err));
            })
          });
        })
      });
    },
    getVttCaptions: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const asset_id = this.$route.params.asset_id;

      fetch(this.DATAPLANE_API_ENDPOINT + '/metadata/' + asset_id + '/WebToVTTCaptions', {
        method: 'get',
        headers: {
          'Authorization': token
        }
      }).then(response => {
        response.json().then(data => ({
            data: data,
          })
        ).then(res => {
          let captions_collection = [];
          this.num_caption_tracks = res.data.results.CaptionsCollection.length;
          res.data.results.CaptionsCollection.forEach(item => {
            // TODO: map the language code to a language label
            const bucket = item.Results.S3Bucket;
            const key = item.Results.S3Key;
            // get URL to captions file in S3
            fetch(this.DATAPLANE_API_ENDPOINT + '/download', {
              method: 'POST',
              mode: 'cors',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': token
              },
              body: JSON.stringify({"S3Bucket": bucket, "S3Key": key})
            }).then(data => {
              data.text().then((data) => {
                captions_collection.push({'src': data, 'lang': item.LanguageCode, 'label': item.LanguageCode});
              }).catch(err => console.error(err));
            })
          });
          this.vttcaptions = captions_collection
        })
      });
    },
    getSrtCaptions: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const asset_id = this.$route.params.asset_id;

      fetch(this.DATAPLANE_API_ENDPOINT + '/metadata/' + asset_id + '/WebToSRTCaptions', {
        method: 'get',
        headers: {
          'Authorization': token
        }
      }).then(response => {
        response.json().then(data => ({
            data: data,
          })
        ).then(res => {
          let captions_collection = [];
          this.num_caption_tracks = res.data.results.CaptionsCollection.length;
          res.data.results.CaptionsCollection.forEach(item => {
            // TODO: map the language code to a language label
            const bucket = item.Results.S3Bucket;
            const key = item.Results.S3Key;
            // get URL to captions file in S3
            fetch(this.DATAPLANE_API_ENDPOINT + '/download', {
              method: 'POST',
              mode: 'cors',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': token
              },
              body: JSON.stringify({"S3Bucket": bucket, "S3Key": key})
            }).then(data => {
              data.text().then((data) => {
                captions_collection.push({'src': data, 'lang': item.LanguageCode, 'label': item.LanguageCode});
              }).catch(err => console.error(err));
            })
          });
          this.srtcaptions = captions_collection
        })
      });
    },
    toHHMMSS(secs) {
      var sec_num = parseInt(secs, 10)
      var hours   = Math.floor(sec_num / 3600)
      var minutes = Math.floor(sec_num / 60) % 60
      var seconds = sec_num % 60

      return [hours,minutes,seconds]
        .map(v => v < 10 ? "0" + v : v)
        .filter((v,i) => v !== "00" || i > 0)
        .join(":")
    },
    sortWebCaptions(item) {
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
    changeStartTime(hms, index) {
      // input time must be in hh:mm:ss or mm:ss format
      let new_time = hms.split(':').reduce((acc,time) => (60 * acc) + +time);
      this.webCaptions[index].start = new_time
      this.sortWebCaptions(this.webCaptions[index])
    },
    changeEndTime(hms, index) {
      // input time must be in hh:mm:ss or mm:ss format
      let new_time = hms.split(':').reduce((acc,time) => (60 * acc) + +time);
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
    handleWaveformSeek() {
      // When user moves the cursor on the waveform
      // then focus the corresponding row in the caption table.
      let timeline_position = this.webCaptions.findIndex(function (item, i) {
        return (parseInt(item.start) <= this.waveform_seek_position && parseInt(item.end) >= this.waveform_seek_position)
      }.bind(this));
      if (timeline_position === -1) {
        // There is no caption at that seek position
        // so just seek to the beginning.
        timeline_position = 0
      }
      if (this.$refs.selectableTable) {
        var element = document.getElementById("caption" + timeline_position);
        element.scrollIntoView();
      }
    },
    handleVideoSeek() {
      // When user moves the cursor on the video player
      // then focus the corresponding row in the caption table.
      if (this.player) {
        this.player.controlBar.progressControl.on('mouseup', function () {
          const current_position = Math.round(this.player.currentTime());
          let timeline_position = this.webCaptions.findIndex(function (item, i) {
            return (parseInt(item.start) <= current_position && parseInt(item.end) >= current_position)
          })
          if (timeline_position === -1) {
            // There is no caption at that seek position
            // so just seek to the beginning.
            timeline_position = 0
          }
          if (this.$refs.selectableTable) {
            var element = document.getElementById("caption" + (timeline_position));
            element.scrollIntoView();
          }
        }.bind(this));
      }
    },
    handleVideoPlay() {
      var last_position = 0;
      // Advance the selected row in the caption table when the video is playing
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
              this.getTxtTranslations();
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
            this.workflow_definition = res.data.Workflow
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
    disableUpstreamStages()  {

      let data = {
        "Name": "MieCompleteWorkflow2",
        "Configuration": this.workflow_config
      }
      data["Input"] = {
        "AssetId": this.asset_id
      };

      let workflow = this.workflow_definition
      let stage_name = workflow.StartAt
      let stage = workflow["Stages"][stage_name]
      let end = false
      while (end == false) {
        console.log("Stage: "+ stage_name)
        if ("End" in stage && stage["End"] == true){
          end = true
        }
        else if (stage_name == "TranslateStage2") {
          end = true
        }
        else {
          // Disable all the operators in the stage
          for (var key in data["Configuration"][stage_name]){
            data["Configuration"][stage_name][key]["Enabled"] = false
            console.log(key + " is disabled")
          }

          stage_name = stage["Next"]
          stage = workflow["Stages"][stage_name]
        }
      }

      return data

    },
    rerunWorkflow: async function (token) {
      // This function reruns all the operators downstream from transcribe.
      let data = this.disableUpstreamStages();

      data["Configuration"]["TranslateStage2"]["TranslateWebCaptions"].MediaType = "MetadataOnly";
      data["Configuration"]["defaultPrelimVideoStage2"]["Thumbnail"].Enabled = true;

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
      const operator_name = "WebCaptions_"+this.selected_lang_code
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
      const blob = new Blob([this.webCaptions_vtt], {type: 'text/plain', endings:'native'});
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
      // Get paginated web captions
      const operator_name = "WebCaptions_"+this.selected_lang_code
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
    pollWorkflowStatus() {
      // Poll frequency in milliseconds
      const poll_frequency = 5000;
      this.workflow_status_polling = setInterval(() => {
        this.getWorkflowStatus();
      }, poll_frequency)
    },
  }
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
</style>

