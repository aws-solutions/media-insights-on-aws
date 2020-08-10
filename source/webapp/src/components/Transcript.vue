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
    <b-alert
        v-model="showVocabularyNotification"
        :variant=vocabularyNotificationStatus
        dismissible
        fade
    >
      {{ vocabularyNotificationMessage }}
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
        <!-- reformat timestamp to hh:mm:ss and -->
        <!-- disable timestamp edits if workflow status is not Complete -->
        <template v-slot:cell(timeslot)="data">
          <b-form-input :disabled="workflow_status !== 'Complete'" class="compact-height start-time-field " :value="toHHMMSS(data.item.start)" @change="new_time => changeStartTime(new_time, data.index)"/>
          <b-form-input :disabled="workflow_status !== 'Complete'" class="compact-height stop-time-field " :value="toHHMMSS(data.item.end)" @change="new_time => changeEndTime(new_time, data.index)"/>
        </template>
        <template v-slot:cell(caption)="data">
          <b-container class="p-0">
            <b-row no-gutters>
              <b-col cols="10">
                <!-- The state on this text area will show a red alert icon
                if the user forgets to enter any text. Otherwise we set the
                state to null so no validity indicator is shown. -->
                <b-form-textarea :disabled="workflow_status !== 'Complete'" :id="'caption' + data.index" :ref="'caption' + data.index" class="custom-text-field .form-control-sm" rows="2" :value="data.item.caption" placeholder="Type subtitle here" :state="(data.item.caption.length > 0) ? null : false" @change="new_caption => changeCaption(new_caption, data.index)" @click='captionClickHandler(data.index)'/>
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
      <br>
<!-- Uncomment to enable Upload button -->
<!--      <b-button id="showModal" size="sm" class="mb-2" @click="showModal()">-->
<!--        <b-icon icon="upload" color="white"></b-icon> Upload JSON-->
<!--      </b-button> &nbsp;-->
      <!-- this is the download button -->
      <b-button id="downloadCaptionsVTT" size="sm" class="mb-2" @click="downloadCaptionsVTT()">
        <b-icon v-if="this.webCaptions.length > 0" icon="download" color="white"></b-icon> Download VTT
      </b-button> &nbsp;
      <!-- this is the save vocabulary button -->
      <b-button id="saveVocabulary" size="sm" class="mb-2" @click="showVocabConfirmation()">
        <b-icon icon="card-text" color="white" ></b-icon>
        Save vocabulary
      </b-button> &nbsp;
      <!-- this is the save edits button for when workflow is paused -->
      <b-button v-if="this.workflow_status === 'Waiting'" id="saveCaptions" size="sm" class="mb-2" @click="saveCaptions()">
        <b-icon v-if="this.isSaving" icon="arrow-clockwise" animation="spin"  color="white"></b-icon>
        <b-icon v-else icon="play" color="white"></b-icon>
        Save edits
      </b-button>
      <!-- this is the save edits button for when workflow complete -->
      <b-button v-if="this.workflow_status === 'Complete' || this.workflow_status === 'Error'" id="editCaptions" size="sm" class="mb-2" @click="showSaveConfirmation()">
        <b-icon icon="play" color="white"></b-icon>
        Save edits
      </b-button>
      <!-- this is the save edits button for when workflow running -->
      <b-button v-if="this.workflow_status === 'Started'" id="editCaptionsDisabled" size="sm" disabled class="mb-2" @click="saveCaptions()">
        <b-icon icon="arrow-clockwise" animation="spin"  color="white"></b-icon>
        Saving edits
      </b-button>
      <b-modal ref="save-modal" title="Save Captions?" @ok="saveCaptions()" ok-title="Confirm">
        <p>Saving captions will restart a workflow that can take several minutes. You will not be able to edit captions until it has finished. Are you ready to proceed?</p>
      </b-modal>
      <b-modal ref="vocab-modal-noop" title="Warning" ok-only>
        <p>Make changes to the captions in order to build the custom vocabulary.
        </p>
        <div slot="modal-title">
          <b-icon icon="exclamation-triangle" variant="danger"></b-icon>
          Vocabulary is empty
        </div>
      </b-modal>
      <b-modal ref="delete-vocab-modal" title="Delete Vocabulary?" @ok="deleteVocabularyRequest()" ok-variant="danger" ok-title="Confirm">
        <p>Are you sure you want to permanently delete the custom vocabulary <b>{{ customVocabularySelected }}</b>?</p>
      </b-modal>
      <b-modal ref="vocab-modal" size="lg" title="Save Vocabulary?" @ok="saveVocabulary()" :ok-disabled="validVocabularyName === false || (customVocabularySelected === '' && customVocabularyCreateNew === '')" ok-title="Save">
        <b-form-group v-if="customVocabularyList.length>0" label="Select a vocabulary to overwrite or specify a new name:">
          <b-form-radio-group
              id="custom-vocab-selection"
              v-model="customVocabularySelected"
              name="custom-vocab-list"
              :options="customVocabularyList"
              text-field="name_and_status"
              value-field="name"
              disabled-field="notEnabled"
              stacked
          >
          </b-form-radio-group>
        </b-form-group>
        <!-- The state on this text area will show a red alert icon if
        the user enters an invalid custom vocabulary name. Otherwise we
        set the state to null so no validity indicator is shown. -->
        <b-form-input v-if="customVocabularyList.length>0" size="sm" v-model="customVocabularyCreateNew" placeholder="Enter new vocabulary name (optional)" :state="validVocabularyName ? null : false"></b-form-input>
        <b-form-input v-else size="sm" v-model="customVocabularyCreateNew" placeholder="Enter new vocabulary name" :state="validVocabularyName ? null : false"></b-form-input>
        <div v-if="validVocabularyName === false" style="color:red">
          Name must be alphanumeric with no spaces.
        </div>
        <div v-if="customVocabularyList.length>0 && customVocabularySelected !== ''">
          Delete the selected vocabulary (optional): <b-button  size="sm" variant="danger" v-b-tooltip.hover.right title="Delete selected vocabulary" @click="deleteVocabulary">Delete</b-button>
        </div>
        <hr>
        <p>Custom vocabulary (click to edit):</p>
        <b-table
          :items="customVocabulary"
          selectable
          select-mode="single"
          fixed responsive="sm"
          bordered
          small
        >
          <!-- This template adds an additional row in the header
 to highlight the fields in the custom vocab schema. -->
          <template v-slot:thead-top="data">
            <b-tr>
              <b-th colspan="1"></b-th>
              <b-th colspan="4" variant="secondary" class="text-center">Custom Vocabulary Fields</b-th>
            </b-tr>
          </template>
          <template v-slot:cell(original_phrase)="row">
          <b-row no-gutters>
            <b-col cols="10">
              <b-form-input v-model="row.item.original_phrase" class="custom-text-field"/>
            </b-col>
          </b-row>
        </template>
        <template v-slot:cell(new_phrase)="row">
          <b-row no-gutters>
            <b-col cols="10">
              <b-form-input v-model="row.item.new_phrase" class="custom-text-field"/>
            </b-col>
          </b-row>
        </template>
        <template v-slot:cell(sounds_like)="row">
          <b-row no-gutters>
            <b-col cols="10">
              <b-form-input v-model="row.item.sounds_like" class="custom-text-field"/>
            </b-col>
          </b-row>
        </template>
        <template v-slot:cell(IPA)="row">
          <b-row no-gutters>
            <b-col cols="10">
              <b-form-input v-model="row.item.IPA" class="custom-text-field"/>
            </b-col>
          </b-row>
        </template>
        <template v-slot:cell(display_as)="row">
          <b-row no-gutters>
          <b-col cols="9">
            <b-form-input v-model="row.item.display_as" class="custom-text-field"/>
          </b-col>
          <b-col nopadding cols="1">
            <span style="position:absolute; top: 0px">
              <b-button size="sm" style="display: flex;" variant="link" v-b-tooltip.hover.right title="Remove row" @click="delete_vocab_row(row.index)">
                <b-icon font-scale=".9" icon="x-circle" color="lightgrey"></b-icon>
              </b-button>
            </span>
            <span style="position:absolute; bottom: 0px">
              <b-button size="sm"  style="display: flex;" variant="link" v-b-tooltip.hover.right title="Add row" @click="add_vocab_row(row.index)">
                <b-icon font-scale=".9" icon="plus-square" color="lightgrey"></b-icon>
              </b-button>
            </span>
          </b-col>
          </b-row>
        </template>
        </b-table>
      </b-modal>

<!-- Uncomment to enable Upload button -->
<!--      <b-modal ref="my-modal" hide-footer title="Upload a file">-->
<!--        <p>Upload a timed subtitles file in the Webcaptions JSON format.</p>-->
<!--        <div>-->
<!--          <input type="file" @change="uploadCaptionsFile">-->
<!--        </div>-->
<!--      </b-modal>-->
      <div style="color:red" v-if="this.webCaptions.length > 0 && this.workflow_status !== 'Complete' && this.workflow_status !== 'Error' && this.workflow_status !== 'Waiting'">
        Editing is disabled until workflow completes.
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
      workflow_definition: {},
      showSaveNotification: 0,
      saveNotificationMessage: "Captions saved",
      showVocabularyNotification: 0,
      vocabularyNotificationStatus: "success",
      vocabularyNotificationMessage: "",
      results: [],
      workflow_status_polling: null,
      vocab_status_polling: null,
      customVocabulary: [],
      customVocabularyList: [],
      customVocabularySelected: "",
      customVocabularyCreateNew: "",
      transcribe_language_code: "",
      vocabulary_used: "",
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
    validVocabularyName: function() {
      // when user begins typing new vocab name, then deselect the radio buttons
      this.customVocabularySelected=""
      const letterNumber = /^[0-9a-zA-Z]+$/;
      // The name can be up to 200 characters long. Valid characters are a-z, A-Z, and 0-9.
      if (this.customVocabularyCreateNew === "" || (this.customVocabularyCreateNew.match(letterNumber) && this.customVocabularyCreateNew.length<200)) {
        return true;
      }
      else
      {
        return false;
      }
    },
    customVocabularyName: function () {
      if (this.customVocabularyCreateNew !== "")
        return this.customVocabularyCreateNew
      else
        return this.customVocabularySelected
    },
    customVocabularyFile: function () {
      let vocab_file = "Phrase\tSoundsLike\tIPA\tDisplayAs"
      for (const i in this.customVocabulary) {
        vocab_file += "\n" + this.customVocabulary[i].new_phrase + "\t\t\t" + this.customVocabulary[i].display_as
      }
      return vocab_file
    },
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
    isProfane() {
      const Filter = require('bad-words');
      const profanityFilter = new Filter({ placeHolder: '_' });
      return profanityFilter.isProfane(this.transcript);
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
    this.isBusy = true;
    this.handleVideoPlay();
    this.handleVideoSeek();
    this.getWorkflowId();
    this.pollWorkflowStatus();
  },
  beforeDestroy: function () {
    this.transcript = ''
    clearInterval(this.workflow_status_polling)
    clearInterval(this.vocab_status_polling)
  },
  methods: {
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
      const Diff = require('diff');
      const diff = Diff.diffWords(this.webCaptions[index].caption, new_caption);
      // if no words were removed (i.e. only new words were added)...
      console.log("Caption edit:")
      console.log(diff)
      let old_word = ''
      let new_word = ''
      for (let i=0; i<=(diff.length-1); i++) {
        // if element contains key removed
        if ("removed" in diff[i] && diff[i].removed !== undefined) {
          old_word += diff[i].value+' '
        }
        // if element contains key added
        else if ("added" in diff[i] && diff[i].added !== undefined) {
          new_word += diff[i].value+' '
        }
        // otherwise if element is just words, or if it's the last element,
        // then save word change to custom vocabulary
        if (i === (diff.length-1) || !("added" in diff[i] || "removed" in diff[i])) {
          // if this value is a space and next value contains key 'added',
          // then break so that we can add that value to the new_word
          if (i !== (diff.length-1) && diff[i].value === ' ' && "added" in diff[i+1] && diff[i+1].added !== 'undefined') {
            continue
          } else {
            // or if this is the last element
            // or if this value is anything other than a space
            // then save to custom vocabulary
            if (old_word != '' && new_word != '') {
              // replace multiple spaces with a single space
              // and remove spaces at beginning or end of word
              old_word = old_word.replace(/ +(?= )/g, '').trim();
              new_word = new_word.replace(/ +(?= )/g, '').trim();
              // transcribe requires numbers to be spelled out in custom vocab phrases,
              // so we derive the number spelling here:
              const converter = require('number-to-words');
              let new_word_with_numbers_as_words = new_word
              if (new_word.match(/\d+/g) != null)
              {
                new_word_with_numbers_as_words = new_word.replace(new_word.match(/\d+/g)[0], converter.toWords(new_word.match(/\d+/g)[0]))
              }
              // remove old_word from custom vocab if it already exists
              this.customVocabulary = this.customVocabulary.filter(function (item) {return item.original_phrase !== old_word;});
              // add old_word to custom vocab
              this.customVocabulary.push({"original_phrase": old_word, "new_phrase": new_word_with_numbers_as_words, "sounds_like":"", "IPA":"", "display_as": new_word})
              console.log("CUSTOM VOCABULARY: " + JSON.stringify(this.customVocabulary))
            }
            old_word = ''
            new_word = ''
          }
        }
      }
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
    webToVtt() {
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
      console.log("workflow status request:")
      console.log('curl -L -k -X GET -H \'Content-Type: application/json\' -H \'Authorization: \''+token+' '+this.WORKFLOW_API_ENDPOINT+'/workflow/execution/asset/' + this.asset_id)
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
            this.transcribe_language_code = res.data.Configuration.defaultAudioStage2.Transcribe.TranscribeLanguage
            this.vocabulary_used = res.data.Configuration.defaultAudioStage2.Transcribe.VocabularyName
            console.log("used vocabulary:")
            console.log(this.vocabulary_used)
            this.$store.commit('updateUsedVocabulary', this.vocabulary_used)
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
      // This function disables all the operators in stages above TranslateStage2
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
        // If the current stage is End then end the loop.
        if ("End" in stage && stage["End"] == true){
              end = true
          }
          // If the current stage is TranslateStage2 then end the loop.
          else if (stage_name == "TranslateStage2") {
              end = true
          }
          // For all other stages disable all the operators in the stage
          else {
              // Disable all the operators in the stage
              for (const operator in data["Configuration"][stage_name]){
                data["Configuration"][stage_name][operator]["Enabled"] = false
                console.log(operator + " is disabled")
              }
              // Now look at the next stage in the workflow
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
    listVocabulariesRequest: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      console.log("List vocabularies request:")
      console.log('curl -L -k -X GET -H \'Content-Type: application/json\' -H \'Authorization: \''+token+' '+this.DATAPLANE_API_ENDPOINT+'/transcribe/list_vocabularies')
      fetch(this.DATAPLANE_API_ENDPOINT + '/transcribe/list_vocabularies', {
        method: 'get',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token
        },
      }).then(response =>
        response.json().then(data => ({
              data: data,
            })
        ).then(res => {
          this.customVocabularyList = res.data["Vocabularies"].map(({VocabularyName, VocabularyState}) => ({
            name: VocabularyName,
            status: VocabularyState,
            name_and_status: VocabularyState === "READY" ? VocabularyName : VocabularyName + " [" + VocabularyState + "]",
            notEnabled: VocabularyState === "PENDING"
          }))
          // if any vocab is PENDING, then poll status until it is not PENDING. This is necessary so custom vocabs become selectable in the GUI as soon as they become ready.
          if (this.customVocabularyList.filter(item => item.status === "PENDING").length > 0) {
            if (this.vocab_status_polling == null) {
              this.pollVocabularyStatus();
            }
          } else {
            if (this.vocab_status_polling != null) {
              clearInterval(this.vocab_status_polling)
              this.vocab_status_polling = null
            }
          }
        })
      )
    },
    deleteVocabulary: async function () {
      this.$refs['delete-vocab-modal'].show()
    },
    deleteVocabularyRequest: async function (token) {
      this.$refs['vocab-modal'].hide()
      if (!token) {
        token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
      }
      this.$refs['delete-vocab-modal'].hide()
      console.log("Delete vocabulary request:")
      console.log('curl -L -k -X POST -H \'Content-Type: application/json\' -H \'Authorization: \''+token+'\' --data \'{"vocabulary_name":"'+this.customVocabularySelected+'}\' '+this.DATAPLANE_API_ENDPOINT+'/transcribe/delete_vocabulary')
      await fetch(this.DATAPLANE_API_ENDPOINT+'/transcribe/delete_vocabulary',{
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': token},
        body: JSON.stringify({"vocabulary_name":this.customVocabularySelected})
      }).then(response =>
        response.json().then(data => ({
              data: data,
              status: response.status
            })
        ).then(res => {
          if (res.status === 200) {
            console.log("Success! Vocabulary deleted.")
            this.vocabularyNotificationMessage = "Deleted vocabulary: " + this.customVocabularySelected
            this.vocabularyNotificationStatus = "success"
            this.showVocabularyNotification = 5
          } else {
            console.log("Failed to delete vocabulary")
            this.vocabularyNotificationMessage = "Failed to delete vocabulary: " + this.customVocabularySelected
            this.vocabularyNotificationStatus = "danger"
            this.showVocabularyNotification = 5
          }
        })
      )
    },
    overwriteVocabularyRequest: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      await this.deleteVocabularyRequest(token).then(() =>
        this.saveVocabularyRequest(token)
      )
    },
    saveVocabularyRequest: async function (token) {
      if (token === null) {
        const token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
      }
      const s3uri = "s3://"+this.DATAPLANE_BUCKET+"/"+this.customVocabularyName
      console.log("Create vocabulary request:")
      console.log('curl -L -k -X POST -H \'Content-Type: application/json\' -H \'Authorization: \''+token+' --data \'{"s3uri":'+s3uri+', "vocabulary_name":'+this.customVocabularyName+', "language_code": '+this.transcribe_language_code+'}\' '+this.DATAPLANE_API_ENDPOINT+'/transcribe/create_vocabulary')
      await fetch(this.DATAPLANE_API_ENDPOINT+'/transcribe/create_vocabulary',{
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': token},
        body: JSON.stringify({"s3uri": s3uri, "vocabulary_name":this.customVocabularyName, "language_code": this.transcribe_language_code})
      }).then(response =>
        response.json().then(data => ({
              data: data,
              status: response.status
            })
        ).then(res => {
          if (res.status === 200) {
            console.log("Success! Custom vocabulary saved.")
            this.vocabularyNotificationMessage = "Saved vocabulary: " + this.customVocabularyName
            this.vocabularyNotificationStatus = "success"
            this.showVocabularyNotification = 5
          } else {
            console.log("Failed to save vocabulary")
            this.vocabularyNotificationMessage = "Failed to save vocabulary: " + this.customVocabularyName
            this.vocabularyNotificationStatus = "danger"
            this.showVocabularyNotification = 5
          }
          // clear the custom vocabulary name used in the save vocab modal form
          this.customVocabularyCreateNew = ''
        })
      )
    },
    saveVocabulary: async function () {
      // This function saves custom vocabulary
      if (this.customVocabularyName === "") {

      }
      this.$refs['vocab-modal'].hide()
      const signedUrl = this.DATAPLANE_API_ENDPOINT + '/upload';
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      // Get presigned url to upload custom vocab file.
      console.log("Pre-signed URL request:")
      console.log("curl -L -k -X POST -H 'Content-Type: application/json' -H 'Authorization: "+token+"' --data '{\"S3Bucket\":\""+this.DATAPLANE_BUCKET+"\",\"S3Key\":\""+this.customVocabularyName+"\"}' "+this.DATAPLANE_API_ENDPOINT+'/upload')
      fetch(signedUrl,{
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': token},
        body: JSON.stringify(
            {"S3Bucket": this.DATAPLANE_BUCKET, "S3Key":this.customVocabularyName}
        )
      }).then(response =>
        response.json().then(data => ({
              data: data,
              status: response.status
            })
        ).then(res => {
          if (res.status === 200) {
            // Now that we have the presigned url, upload the custom vocab file.
            res.data.fields["file"] = this.customVocabularyFile
            console.log("Upload request:")
            let curl_command = "curl --request POST"
            for (let key in res.data.fields) {
              curl_command += " -F " + key + "=\""+res.data.fields[key]+"\""
            }
            curl_command += " " + res.data.url
            console.log(curl_command)
            let formData  = new FormData();
            for(const name in res.data.fields) {
              formData.append(name, res.data.fields[name]);
            }
            fetch(res.data.url, {
              method: 'POST',
              body: formData
            }).then(() => {
              // Now that the custom vocab file is in s3, create the custom vocab in AWS Transcribe.
              // If the custom vocab already exists then overwrite it.
              if (this.customVocabularyList.some(item => item.name === this.customVocabularyName)) {
                console.log("Overwriting custom vocabulary")
                this.overwriteVocabularyRequest(token)
              } else {
                this.saveVocabularyRequest(token)
              }
            })
          }
        })
        )
    },
    saveCaptions: async function () {
      // This function saves captions to the dataplane
      // and reruns or resumes the workflow.
      this.$refs['save-modal'].hide()
      this.isSaving=true;
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
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
    showVocabConfirmation: async function() {
      if (this.customVocabulary.length > 0){
        await this.listVocabulariesRequest()
        this.$refs['vocab-modal'].show()
      } else {
        this.$refs['vocab-modal-noop'].show()
      }
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
            console.log("ERROR: Failed to download captions.");
            console.log(res.data.Code);
            console.log(res.data.Message);
            console.log("Response: " + res.status);
            this.isBusy = false
            this.noTranscript = true
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
    add_vocab_row(index) {
      this.customVocabulary.splice(index+1, 0, {})
    },
    delete_vocab_row(index) {
      this.customVocabulary.splice(index, 1)
    },
    pollWorkflowStatus() {
      // Poll frequency in milliseconds
      const poll_frequency = 5000;
      this.workflow_status_polling = setInterval(() => {
        this.getWorkflowStatus();
      }, poll_frequency)
    },
    pollVocabularyStatus() {
      // Poll frequency in milliseconds
      const poll_frequency = 10000;
      this.vocab_status_polling = setInterval(() => {
        this.listVocabulariesRequest();
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
    padding-left: 0px !important;
    padding-right: 0px !important;
    margin-top: 0px !important;
    margin-bottom: 0px !important;
  }
  tr.b-table-row-selected {
    border-left: 1px solid #cc181e !important;
  }
  table.b-table-selectable > tbody > tr.b-table-row-selected > td {
    background-color: white !important;
  }
</style>
