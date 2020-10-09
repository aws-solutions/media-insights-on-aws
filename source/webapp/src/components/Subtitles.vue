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
      :variant="vocabularyNotificationStatus"
      dismissible
      fade
    >
      {{ vocabularyNotificationMessage }}
    </b-alert>
    <b-modal ref="vocab-modal" size="lg" title="Save Vocabulary?" :ok-disabled="validVocabularyName === false || (customVocabularySelected === '' && customVocabularyCreateNew === '') || customVocabularyUnion.length === 0" ok-title="Save" @ok="saveVocabulary()">
      <b-row>
        <b-col>
          <b>Select a vocabulary to overwrite:</b>
          <b-form-group v-if="customVocabularyList.length>0">
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
          <div v-if="customVocabularyList.length > 0 && customVocabularySelected !== ''">
            Delete the selected vocabulary (optional): <b-button v-b-tooltip.hover.right size="sm" title="Delete selected vocabulary" variant="danger" @click="deleteVocabulary">
            Delete
          </b-button>
          </div>
        </b-col>
        <b-col>
          <b>Or create a new vocabulary:</b><br>
          <!-- The state on this text area will show a red alert icon if
    the user enters an invalid custom vocabulary name. Otherwise we
    set the state to null so no validity indicator is shown. -->
          Vocabulary Name:
          <b-form-input v-if="customVocabularyList.length>0" v-model="customVocabularyCreateNew" size="sm" placeholder="Enter vocabulary name (optional)" :state="validVocabularyName ? null : false" @focus="customVocabularySelected=''"></b-form-input>
          <b-form-input v-else v-model="customVocabularyCreateNew" size="sm" placeholder="Enter vocabulary name" :state="validVocabularyName ? null : false"></b-form-input>
          Vocabulary Language:
          <b-form-select
            v-model="vocabulary_language_code"
            :options="transcribeLanguages"
            size="sm"
          />
          <hr>
          <label>Draft vocabulary name: </label> {{ customVocabularyName }}
          <div v-if="customVocabularySelected === '' && customVocabularyCreateNew === ''" style="color:red">
            Select a vocabulary name or specify a new vocabulary name.
          </div>
          <br>
          <label>Draft vocabulary language:</label> {{ vocabulary_language_code }}
        </b-col>
      </b-row>
      <hr>
      <div v-if="customVocabularyUnsaved.length !== 0">
        Draft vocabulary (click to edit):
        <div v-if="customVocabularySelected != ''" class="text-info" style="font-size: 80%">
          Rows shown in blue are from vocabulary, <b>{{ customVocabularySelected }}.</b>
        </div>
      </div>
      <b-table
        :items="customVocabularyUnion"
        :fields="customVocabularyFields"
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
            <b-th colspan="4" variant="secondary" class="text-center">
              Custom Vocabulary Fields
            </b-th>
          </b-tr>
        </template>
        <template v-slot:cell(original_phrase)="row">
          <b-row no-gutters>
            <b-col cols="10">
              <div v-if="row.index < customVocabularyUnsaved.length">
                <b-form-input v-model="row.item.original_phrase" class="custom-text-field" :formatter="phrase_formatter" lazy-formatter />
              </div>
              <div v-else>
                <b-form-input v-model="row.item.original_phrase" class="custom-text-field text-info" :formatter="phrase_formatter" lazy-formatter />
              </div>
            </b-col>
          </b-row>
        </template>
        <template v-slot:cell(new_phrase)="row">
          <b-row no-gutters>
            <b-col cols="10">
              <div v-if="row.index < customVocabularyUnsaved.length">
                <b-form-input v-model="row.item.new_phrase" class="custom-text-field" :formatter="phrase_formatter" lazy-formatter />
              </div>
              <div v-else>
                <b-form-input v-model="row.item.new_phrase" class="custom-text-field text-info" :formatter="phrase_formatter" lazy-formatter />
              </div>
            </b-col>
          </b-row>
        </template>
        <template v-slot:cell(sounds_like)="row">
          <b-row no-gutters>
            <b-col cols="10">
              <div v-if="row.index < customVocabularyUnsaved.length">
                <b-form-input v-model="row.item.sounds_like" class="custom-text-field" />
              </div>
              <div v-else>
                <b-form-input v-model="row.item.sounds_like" class="custom-text-field text-info" />
              </div>
            </b-col>
          </b-row>
        </template>
        <template v-slot:cell(IPA)="row">
          <b-row no-gutters>
            <b-col cols="10">
              <div v-if="row.index < customVocabularyUnsaved.length">
                <b-form-input v-model="row.item.IPA" class="custom-text-field" />
              </div>
              <div v-else>
                <b-form-input v-model="row.item.IPA" class="custom-text-field text-info" />
              </div>
            </b-col>
          </b-row>
        </template>
        <template v-slot:cell(display_as)="row">
          <b-row no-gutters>
            <b-col cols="9">
              <div v-if="row.index < customVocabularyUnsaved.length">
                <b-form-input v-model="row.item.display_as" class="custom-text-field" />
              </div>
              <div v-else>
                <b-form-input v-model="row.item.display_as" class="custom-text-field text-info" />
              </div>
            </b-col>
            <b-col nopadding cols="1">
              <span style="position:absolute; top: 0px">
                <b-button v-b-tooltip.hover.right size="sm" style="display: flex;" variant="link" title="Remove row" @click="delete_vocab_row(row.index)">
                  <b-icon font-scale=".9" icon="x-circle" color="lightgrey"></b-icon>
                </b-button>
              </span>
              <span style="position:absolute; bottom: 0px">
                <b-button v-b-tooltip.hover.right size="sm" style="display: flex;" variant="link" title="Add row" @click="add_vocab_row(row.index)">
                  <b-icon font-scale=".9" icon="plus-square" color="lightgrey"></b-icon>
                </b-button>
              </span>
            </b-col>
          </b-row>
        </template>
      </b-table>
      <div v-if="customVocabularyUnion.length === 0 && customVocabularyList.length !== 0" style="color:red">
        Select an existing vocabulary.<br>
      </div>
      <div v-if="customVocabularyUnion.length === 0 && customVocabularyList.length === 0" style="color:red">
        Make changes to the subtitles in order to build a custom vocabulary.<br>
      </div>
      <div v-else-if="validVocabularyName === false" style="color:red">
        Invalid vocabulary name. Valid characters are a-z, A-Z, and 0-9. Max length is 200.
      </div>
    </b-modal>
    <b-modal ref="save-modal" ok-title="Confirm" title="Save Captions?" @ok="saveCaptions()">
      <p>Saving captions will restart a workflow that can take several minutes. You will not be able to edit captions until it has finished. Are you ready to proceed?</p>
    </b-modal>
    <b-modal ref="delete-vocab-modal" ok-title="Confirm" ok-variant="danger" title="Delete Vocabulary?" @ok="deleteVocabularyRequest(token=null, customVocabularyName=customVocabularySelected)">
      <p>Are you sure you want to permanently delete the custom vocabulary <b>{{ customVocabularySelected }}</b>?</p>
    </b-modal>

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
          ref="selectableTable"
          selectable
          fixed
          select-mode="single"
          thead-class="hidden_header"
          responsive="sm"
          :items="webCaptions"
          :fields="webCaptions_fields"
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
            <b-form-input :disabled="workflow_status !== 'Complete'" class="compact-height start-time-field " :value="toHHMMSS(data.item.start)" @change="new_time => changeStartTime(new_time, data.index)" />
            <b-form-input :disabled="workflow_status !== 'Complete'" class="compact-height stop-time-field " :value="toHHMMSS(data.item.end)" @change="new_time => changeEndTime(new_time, data.index)" />
          </template>
          <template v-slot:cell(caption)="data">
            <b-container class="p-0">
              <b-row no-gutters>
                <b-col cols="10">
                  <!-- The state on this text area will show a red alert icon
                  if the user forgets to enter any text. Otherwise we set the
                  state to null so no validity indicator is shown. -->
                  <b-form-textarea :id="'caption' + data.index" :ref="'caption' + data.index" :disabled="workflow_status !== 'Complete'" class="custom-text-field .form-control-sm" rows="2" :value="data.item.caption" placeholder="Type subtitle here" :state="(data.item.caption.length > 0) ? null : false" @change="new_caption => changeCaption(new_caption, data.index)" @click="captionClickHandler(data.index)" />
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
      <b-button v-if="webCaptions.length > 0" id="downloadCaptionsVTT" size="sm" class="mb-2" @click="downloadCaptionsVTT()">
        <b-icon icon="download" color="white"></b-icon> Download VTT
      </b-button> &nbsp;
      <!-- this is the save vocabulary button -->
      <b-button id="saveVocabulary" v-b-tooltip.hover title="Save vocabulary will open a window where you can create or modify custom vocabularies for AWS Transcribe" size="sm" class="mb-2" @click="showVocabConfirmation()">
        <b-icon icon="card-text" color="white"></b-icon>
        Save vocabulary
      </b-button> &nbsp;
      <!-- this is the save edits button for when workflow is paused -->
      <b-button v-if="workflow_status === 'Waiting'" id="saveCaptions" size="sm" class="mb-2" @click="saveCaptions()">
        <b-icon v-if="isSaving" icon="arrow-clockwise" animation="spin" color="white"></b-icon>
        <b-icon v-else icon="play" color="white"></b-icon>
        Save edits
      </b-button>
      <!-- this is the save edits button for when workflow complete -->
      <b-button v-if="workflow_status === 'Complete' || workflow_status === 'Error'" id="editCaptions" v-b-tooltip.hover title="Save edits will regenerate the VTT and SRT caption files so they include any changes you may have made to captions." size="sm" class="mb-2" @click="showSaveConfirmation()">
        <b-icon icon="play" color="white"></b-icon>
        Save edits
      </b-button>
      <!-- this is the save edits button for when workflow running -->
      <b-button v-if="workflow_status === 'Started'" id="editCaptionsDisabled" size="sm" disabled class="mb-2" @click="saveCaptions()">
        <b-icon icon="arrow-clockwise" animation="spin" color="white"></b-icon>
        Saving edits
      </b-button>

      <!-- Uncomment to enable Upload button -->
      <!--      <b-modal ref="my-modal" hide-footer title="Upload a file">-->
      <!--        <p>Upload a timed subtitles file in the Webcaptions JSON format.</p>-->
      <!--        <div>-->
      <!--          <input type="file" @change="uploadCaptionsFile">-->
      <!--        </div>-->
      <!--      </b-modal>-->
      <div v-if="webCaptions.length > 0 && workflow_status !== 'Complete' && workflow_status !== 'Error' && workflow_status !== 'Waiting'" style="color:red">
        Editing is disabled until workflow completes.
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
const converter = require('number-to-words');

export default {
  name: "Subtitles",
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
      customVocabularyUnsaved: [],
      customVocabularySaved: [],
      customVocabularyFields: ["original_phrase","new_phrase","sounds_like","IPA","display_as"],
      customVocabularyList: [],
      customVocabularySelected: "",
      customVocabularyCreateNew: "",
      transcribe_language_code: "",
      vocabulary_language_code: "",
      vocabulary_used: "",
      vocabulary_uri: null,
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
      noTranscript: false,
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
      ]
    }
  },
  computed: {
    customVocabularyUnion: function() {
      return this.customVocabularyUnsaved.concat(this.customVocabularySaved)
    },
    validVocabularyName: function() {
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
      let customVocabularyUnion = this.customVocabularyUnion
      for (const i in customVocabularyUnion) {
        if (customVocabularyUnion[i].new_phrase === undefined)
          customVocabularyUnion[i].new_phrase = ""
        if (customVocabularyUnion[i].sounds_like === undefined)
          customVocabularyUnion[i].sounds_like = ""
        if (customVocabularyUnion[i].IPA === undefined)
          customVocabularyUnion[i].IPA = ""
        if (customVocabularyUnion[i].display_as === undefined)
          customVocabularyUnion[i].display_as = ""
      }

      let vocab_file = "Phrase\tSoundsLike\tIPA\tDisplayAs"
      for (const i in customVocabularyUnion) {
        vocab_file += "\n" + customVocabularyUnion[i].new_phrase + "\t" + customVocabularyUnion[i].sounds_like + "\t" + customVocabularyUnion[i].IPA + "\t" + customVocabularyUnion[i].display_as
      }
      console.log("vocabulary file")
      console.log(vocab_file)
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
    ...mapState(['player', 'waveform_seek_position', 'unsaved_custom_vocabularies']),
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
    // when user begins typing new vocab name, then deselect the radio buttons
    customVocabularyCreateNew: function() {
      this.customVocabularySelected = ""
    },
    customVocabularySelected: async function() {
      // Remove phrases from the previously selected vocabulary
      // before we add phrases from the newly selected vocabulary.
      if (this.customVocabularySelected !== "") {
        // update the vocabulary language shown in the web form.
        this.vocabulary_language_code = this.customVocabularyList.filter(item => (item.name === this.customVocabularySelected))[0].language_code
        // add phrases from the selected vocabulary
        await this.downloadVocabulary()
      }

    }
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
    this.getWorkflowStatus();
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
      // We're using the diff package to determine what words were added or removed from the subtitles
      const Diff = require('diff');
      const diff = Diff.diffWords(this.webCaptions[index].caption, new_caption);
      // Diff returns a dictionary that contains "added" or "removed" keys for words
      // which were added or removed. So, we'll look for those keys now:
      console.log("Caption edit:")
      console.log(diff)
      let old_phrase = ''
      let new_phrase = ''
      let next_word = ''
      for (let i=0; i<=(diff.length-1); i++) {
        // If element contains key removed
        if ("removed" in diff[i] && diff[i].removed !== undefined) {
          old_phrase += diff[i].value+' '
        }
        // If element contains key added
        else if ("added" in diff[i] && diff[i].added !== undefined) {
          new_phrase += diff[i].value+' '
        }
        // If the element is the last element and
        // does not contain "removed" or "added" keys, then it
        // contains the text that follows the edited phrase.
        else if (i === diff.length - 1) {
          next_word = diff[i].value.trim().split(" ")[0]
          console.log("next word: " + next_word)
        }
        // otherwise if element is just words, or if it's the last element,
        // then save word change to custom vocabulary
        if (i === (diff.length-1) || !("added" in diff[i] || "removed" in diff[i])) {
          // if this value is a space and next value contains key 'added',
          // then break so that we can add that value to the new_phrase
          if (i !== (diff.length-1) && diff[i].value === ' ' && "added" in diff[i+1] && diff[i+1].added !== 'undefined') {
            continue
          } else {
            // or if this is the last element
            // or if this value is anything other than a space
            // then save to custom vocabulary
            if (old_phrase != '' && new_phrase != '') {
              // replace multiple spaces with a single space
              // and remove spaces at beginning or end of word
              old_phrase = old_phrase.replace(/ +(?= )/g, '').trim();
              new_phrase = new_phrase.replace(/ +(?= )/g, '').trim();
              // If the edited phrase ends with a apostrophe or a hyphen,
              // then we'll concatenate that phrase with the first word in
              // the text that follows the edited phrase. We need to do this
              // because the custom vocabulary will fail to save if it
              // contains any phrases that end with an apostrophe or a hyphen.
              if (new_phrase.slice(-1).match(/[',-]/i)) {
                new_phrase = new_phrase + next_word
              }
              // Transcribe requires numbers to be spelled out in the phrase field.
              // Transcribe also requires spaces to be dashes in the phrase field.
              // So we make those changes here:
              let new_phrase_with_numbers_as_words = this.phrase_formatter(new_phrase)
              // remove old_phrase from custom vocab, if it already exists
              this.customVocabularyUnsaved = this.customVocabularyUnsaved.filter(item => {return item.original_phrase !== old_phrase;});
              // add old_phrase to custom vocab
              this.customVocabularyUnsaved.push({"original_phrase": old_phrase, "new_phrase": new_phrase_with_numbers_as_words, "sounds_like":"", "IPA":"", "display_as": new_phrase})
              console.log("CUSTOM VOCABULARY: " + JSON.stringify(this.customVocabularyUnsaved))
            }
            old_phrase = ''
            new_phrase = ''
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
      let timeline_position = this.webCaptions.findIndex(function (item) {
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
          let timeline_position = this.webCaptions.findIndex(function (item) {
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
          let timeline_position = this.webCaptions.findIndex(function(item){return (parseInt(item.start) <= current_position && parseInt(item.end) >= current_position)})
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
      // This function gets the source language from the workflow configuration
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
          this.vocabulary_language_code = this.transcribe_language_code
          this.vocabulary_used = res.data.Configuration.defaultAudioStage2.Transcribe.VocabularyName
          const operator_info = []
          const transcribe_language = this.transcribeLanguages.filter(x => (x.value === this.transcribe_language_code))[0].text;
          operator_info.push({"name": "Source Language", "value": transcribe_language})
          if (this.vocabulary_used) {
            operator_info.push({"name": "Custom Vocabulary", "value": this.vocabulary_used})
          }
          this.$store.commit('updateOperatorInfo', operator_info)
          this.getWebCaptions()
          }
        )
        }
      )
    },
    downloadVocabulary: async function() {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      console.log("Get vocabulary request:")
      console.log('curl -L -k -X POST -H \'Content-Type: application/json\' -H \'Authorization: \''+token+' --data \'{"vocabulary_name":"'+this.customVocabularySelected+'"}\' '+this.DATAPLANE_API_ENDPOINT+'/transcribe/download_vocabulary')
      fetch(this.DATAPLANE_API_ENDPOINT + '/transcribe/download_vocabulary', {
        method: 'post',
        mode: 'cors',
        body: JSON.stringify({"vocabulary_name":this.customVocabularySelected}),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token
        },
      }).then(response =>
        response.json().then(data => ({
          data: data,
          status: response.status
          })
        ).then(res => {
          if(res.status == 200) {
            // save phrases from the currently selected vocabulary
            this.customVocabularySaved = res.data.vocabulary.map(({Phrase, SoundsLike, IPA, DisplayAs}) => ({
              original_phrase: "",
              new_phrase: Phrase,
              sounds_like: SoundsLike,
              IPA: IPA,
              display_as: DisplayAs
            }));
          } else {
            console.log("WARNING: Could not download vocabulary. Loading vocab from vuex state...")
            this.customVocabularySaved = this.unsaved_custom_vocabularies.filter(item => (item.Name === this.customVocabularySelected))[0].vocabulary
          }
        })
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
            this.pollWorkflowStatus()
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
          this.customVocabularyList = res.data["Vocabularies"].map(({VocabularyName, VocabularyState, LanguageCode}) => ({
            name: VocabularyName,
            status: VocabularyState,
            language_code: LanguageCode,
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
    deleteVocabularyRequest: async function (token, customVocabularyName) {
      if (!token) {
        token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
      }
      this.$refs['delete-vocab-modal'].hide()
      console.log("Delete vocabulary request:")
      console.log('curl -L -k -X POST -H \'Content-Type: application/json\' -H \'Authorization: \''+token+'\' --data \'{"vocabulary_name":"'+customVocabularyName+'}\' '+this.DATAPLANE_API_ENDPOINT+'/transcribe/delete_vocabulary')
      await fetch(this.DATAPLANE_API_ENDPOINT+'/transcribe/delete_vocabulary',{
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': token},
        body: JSON.stringify({"vocabulary_name":customVocabularyName})
      }).then(response =>
        response.json().then(data => ({
              data: data,
              status: response.status
            })
        ).then(res => {
          if (res.status === 200) {
            console.log("Success! Vocabulary deleted.")
            this.vocabularyNotificationMessage = "Deleted vocabulary: " + customVocabularyName
            this.vocabularyNotificationStatus = "success"
            this.showVocabularyNotification = 5
            // reset the radio button selection
            this.customVocabularySelected = ""
            this.customVocabularySaved = []
            this.listVocabulariesRequest()
          } else {
            console.log("Failed to delete vocabulary")
            this.vocabularyNotificationMessage = "Failed to delete vocabulary: " + customVocabularyName
            this.vocabularyNotificationStatus = "danger"
            this.showVocabularyNotification = 5
          }
        })
      )
    },
    overwriteVocabularyRequest: async function (token, customVocabularyName) {
      if (token === null) {
        token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
      }
      await this.deleteVocabularyRequest(token, customVocabularyName).then(() => {
        this.saveVocabularyRequest(token, customVocabularyName)
      })
    },
    saveVocabularyRequest: async function (token, customVocabularyName) {
      if (token === null) {
        token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
      }
      const s3uri = "s3://"+this.DATAPLANE_BUCKET+"/"+customVocabularyName
      console.log("Create vocabulary request:")
      console.log('curl -L -k -X POST -H \'Content-Type: application/json\' -H \'Authorization: \''+token+' --data \'{"s3uri":'+s3uri+', "vocabulary_name":'+customVocabularyName+', "language_code": '+this.transcribe_language_code+'}\' '+this.DATAPLANE_API_ENDPOINT+'/transcribe/create_vocabulary')
      await fetch(this.DATAPLANE_API_ENDPOINT+'/transcribe/create_vocabulary',{
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': token},
        body: JSON.stringify({"s3uri": s3uri, "vocabulary_name":customVocabularyName, "language_code": this.vocabulary_language_code})
      }).then(response =>
        response.json().then(data => ({
              data: data,
              status: response.status
            })
        ).then(res => {
          if (res.status === 200) {
            console.log("Saving custom vocabulary...")
            this.vocabularyNotificationMessage = "Saving custom vocabulary " + customVocabularyName + "..."
            this.vocabularyNotificationStatus = "success"
            this.showVocabularyNotification = 5
            this.customVocabularyUnsaved = []
          } else {
            console.log("Failed to save vocabulary")
            this.vocabularyNotificationMessage = "Failed to save vocabulary: " + customVocabularyName
            this.vocabularyNotificationStatus = "danger"
            this.showVocabularyNotification = 5
          }
          // clear the custom vocabulary name used in the save vocab modal form
          this.customVocabularyCreateNew = ''
        })
      )
    },
    saveVocabulary: async function () {
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
              const customVocabularyName = this.customVocabularyName
              if (this.customVocabularyList.some(item => item.name === this.customVocabularyName)) {
                console.log("Overwriting custom vocabulary: " + customVocabularyName)
                this.overwriteVocabularyRequest(token, customVocabularyName)
              } else {
                this.saveVocabularyRequest(token, customVocabularyName)
              }
              // Save custom vocabulary to vuex state so we can reload it
              // if Transcribe failed to save it.
              let unsavedCustomVocabularies = this.unsaved_custom_vocabularies
              // Delete any vocabs in vuex state with the same name
              // as the current one being saved.
              unsavedCustomVocabularies = this.unsaved_custom_vocabularies.filter(item => (item.Name !== customVocabularyName))
              // Save the unsaved vocab in vuex state.
              unsavedCustomVocabularies = unsavedCustomVocabularies.concat({"Name":customVocabularyName, "vocabulary":this.customVocabularyUnion})
              this.$store.commit('updateUnsavedCustomVocabularies', unsavedCustomVocabularies);
            })
          }
        })
        )
    },
    saveCaptions: async function () {
      // This function saves captions to the dataplane
      // and reruns or resumes the workflow.
      this.isSaving=true;
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const operator_name = "WebCaptions_"+this.sourceLanguageCode
      const webCaptions = {"WebCaptions": this.webCaptions}
      console.log("this.webCaptions")
      console.log(JSON.stringify(this.webCaptions))
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
            clearInterval(this.workflow_status_polling)
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
      await this.listVocabulariesRequest()
      this.$refs['save-modal'].hide()
      this.$refs['vocab-modal'].show()
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
            console.log("low confidence words:")
            // TODO: highlight low confidence words in GUI
            const low_confidence_words = []
            const confidence_threshold = 0.90
            console.log("confidence threshold: " + confidence_threshold)
            this.webCaptions.forEach(item => {
              item.wordConfidence.filter(word => word.c < "0.99")
                .forEach(word => {
                  // add low confidence word to array if it hasn't already been added
                  if (low_confidence_words.includes(word.w) === false) {
                    low_confidence_words.push(word.w)
                  }
                })
            })
            console.log(low_confidence_words)
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
      // The index provided is the index into the concatenated unsaved and saved vocabularies
      // Unsaved vocab will always be listed first, so we convert the index as follows so that
      // we can splice appropriately in the unsaved or saved vocabulary.
      if (index < this.customVocabularyUnsaved.length) {
        this.customVocabularyUnsaved.splice(index+1, 0, {})
      } else {
        this.customVocabularyUnsaved.splice(index-this.customVocabularyUnsaved.length, 0, {})      }
    },
    delete_vocab_row(index) {
      // The index provided is the index into the concatenated unsaved and saved vocabularies
      // Unsaved vocab will always be listed first, so we convert the index as follows so that
      // we can splice appropriately in the unsaved or saved vocabulary.
      if (index < this.customVocabularyUnsaved.length) {
        this.customVocabularyUnsaved.splice(index, 1)
      } else {
        const index_into_saved_vocab = index - this.customVocabularyUnsaved.length
        this.customVocabularySaved.splice(index_into_saved_vocab, 1)
      }
      if (this.customVocabularyUnion.length === 0){
        this.customVocabularyUnsaved = [{"original_phrase":"","new_phrase":"","sounds_like":"","IPA":"","display_as":""}]
      }
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
    phrase_formatter(phrase) {
      // Transcribe requires numbers to be spelled out in the phrase field.
      // Transcribe also requires spaces to be dashes in the phrase field.
      // This function will automatically make those changes for user input to the phrase field.
      let phrase_with_numbers_as_words = phrase
      if (phrase.match(/\d+/g) != null)
      {
        phrase_with_numbers_as_words = phrase
          .replace(phrase.match(/\d+/g)[0], converter.toWords(phrase.match(/\d+/g)[0]))
          .replace(/,/g, '')
      }
      return phrase_with_numbers_as_words.replace(/\s+/g, '-')
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
