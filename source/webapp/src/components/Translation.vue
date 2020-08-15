<template>
  <div>
    <div v-if="noTranslation === true">
      No translation found for this asset
    </div>
    <!-- show spinner while busy loading -->
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
    <!-- show table if not busy loading and translation data exists -->
    <div
      v-else-if="noTranslation === false"
      class="wrapper"
    >
      <!-- show radio buttons for each available translation language -->
      <b-form-group>
        <b-form-radio-group
          v-model="selected_lang_code"
          :options="alphabetized_language_collection"
          @change="getWebCaptions"
        ></b-form-radio-group>
      </b-form-group>
      <!-- show translation text when language has been selected -->
      <div v-if="selected_lang_code !== ''" id="event-line-editor" class="event-line-editor">
        <b-table
          ref="selectableTable"
          selectable
          select-mode="single"
          thead-class="hidden_header"
          fixed responsive="sm"
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
                  <!-- The state on this text area will show a red alert icon if the user forgets to enter any text. Otherwise we set the state to null so no validity indicator is shown. -->
                  <b-form-textarea
                    :id="'caption' + data.index"
                    :ref="'caption' + data.index"
                    class="custom-text-field .form-control-sm"
                    rows="2"
                    placeholder="Type translation here"
                    :value="data.item.caption"
                    :dir="text_direction"
                    :disabled="workflow_status !== 'Complete'"
                    :state="(data.item.caption.length > 0) ? null : false"
                    @change="new_caption => changeCaption(new_caption, data.index)"
                    @click="captionClickHandler(data.index)"
                  />
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
      <!-- this is the download button -->
      <b-dropdown id="download-dropdown" text="Download VTT/SRT" class="mb-2" size="sm" dropup no-caret>
        <template slot="button-content">
          <b-icon icon="download" color="white"></b-icon> Download
        </template>
        <b-dropdown-item :href="vtt_url">
          Download VTT
        </b-dropdown-item>
        <b-dropdown-item :href="srt_url">
          Download SRT
        </b-dropdown-item>
        <b-dropdown-item v-if="pollyaudio_url" :href="pollyaudio_url" target="_blank" download>
          Download Audio
        </b-dropdown-item>
        <b-dropdown-item v-else disabled>
          Download Audio (language not supported)
        </b-dropdown-item>
      </b-dropdown>
      &nbsp;
      <!-- this is the save edits button for when workflow complete -->
      <b-button v-if="workflow_status === 'Complete' || workflow_status === 'Error'" id="editCaptions" size="sm" class="mb-2" @click="saveCaptions()">
        <b-icon icon="play" color="white"></b-icon>
        Save edits
      </b-button>
      <!-- this is the save edits button for when workflow running -->
      <b-button v-else id="editCaptionsDisabled" size="sm" disabled class="mb-2">
        <b-icon icon="arrow-clockwise" animation="spin" color="white"></b-icon>
        Saving edits
      </b-button>
      <br>
      <b-modal ref="save-modal" title="Save Confirmation" ok-title="Confirm" @ok="saveCaptions()">
        <p>Saving will overwrite the existing {{ selected_lang }} translation. Are you sure?</p>
      </b-modal>
      <div v-if="webCaptions.length > 0 && workflow_status !== 'Complete' && workflow_status !== 'Error' && workflow_status !== 'Waiting'" style="color:red">
        Editing is disabled until workflow completes.
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
      text: "",
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
      pollyaudiotranscripts: [
        {
          src: "",
          lang: "",
          label: ""
        }
      ],
      isBusy: false,
      operator: "translation",
      noTranslation: false,
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
      let translationsCollection = this.translationsCollection
      return translationsCollection.sort(function(a, b) {
        const textA = a.text.toUpperCase();
        const textB = b.text.toUpperCase();
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
      return null
    },
    srt_url: function() {
      if (this.selected_lang_code !== '') {
        let srtcaption = this.srtcaptions.filter(x => (x.lang === this.selected_lang_code))[0];
        if (srtcaption) {
          return srtcaption.src
        }
      }
      return null
    },
    pollyaudio_url: function() {
      if (this.selected_lang_code !== '') {
        let pollyaudiotranscript = this.pollyaudiotranscripts.filter(x => (x.lang === this.selected_lang_code))[0];
        if (pollyaudiotranscript) {
          return pollyaudiotranscript.src
        } else {
        return null
        }
      } else {
        return null
      }
    },
    text_direction: function() {
      // This function is used to change text direction for right-to-left languages
      if (this.selected_lang_code === "ar" || this.selected_lang_code === "fa" || this.selected_lang_code === "he" || this.selected_lang_code === "ur" ) return "rtl"
      else return "ltr"
    }
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
    this.selected_lang_code = ""
  },
  activated: function () {
    console.log('activated component:', this.operator);
    this.getVttCaptions();
    this.getSrtCaptions();
    this.getPollyAudioTranscripts()
    this.isBusy = true;
    this.handleVideoPlay();
    this.handleVideoSeek();
    this.getWorkflowId();
    this.pollWorkflowStatus();
  },
  beforeDestroy: function () {
    },
  methods: {
    getLanguageList: async function () {
      // This function gets the list of languages that the user can choose from
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      this.translationsCollection = [];
      const asset_id = this.$route.params.asset_id;
      // Get the all the output for the TranslateWebCaptions operator.
      // We do this simply so we can get the list of languages that have been translated.
      fetch(this.DATAPLANE_API_ENDPOINT + '/metadata/' + asset_id + '/TranslateWebCaptions', {
        method: 'get',
        headers: {
          'Authorization': token
        }
      }).then(response => {
        response.json().then(data => ({
            data: data,
          })
        ).then(async (res) => {
          // get the list of available languages
          res.data.results.CaptionsCollection.forEach( (item) => {
            let languageLabel = this.translateLanguages.filter(x => (x.value === item.TargetLanguageCode))[0].text;
            // save the language code to the translationsCollection
            this.translationsCollection.push(
              {text: languageLabel, value: item.TargetLanguageCode}
            );
          })
          // Got all the languages now.
          // Set the default language to the first one in the alphabetized list.
          if (this.alphabetized_language_collection.length > 0) {
            this.selected_lang = this.alphabetized_language_collection[0].text
            this.selected_lang_code = this.alphabetized_language_collection[0].value
            await this.getWebCaptions()
          }
          this.isBusy = false
        })
      });
    },
    asyncForEach: async function(array, callback) {
      // This async function allows us to wait for all vtt files to be
      // downloaded.
      for (let index = 0; index < array.length; index++) {
        await callback(array[index]);
      }
    },
    getVttCaptions: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const asset_id = this.$route.params.asset_id;
      // get the WebToVTTCaptions metadata json file that
      // contains the list of paths to vtt files in s3
      fetch(this.DATAPLANE_API_ENDPOINT + '/metadata/' + asset_id + '/WebToVTTCaptions', {
        method: 'get',
        headers: {
          'Authorization': token
        }
      }).then(response => {
        response.json().then(data => ({
            data: data,
            status: response.status
          })
        ).then(res => {
          if (res.status !== 200) {
            this.isBusy = false
            this.noTranslation = true
            console.log("ERROR: Could not retrieve Translation data.");
            console.log(res.data.Code);
            console.log(res.data.Message);
            console.log("URL: " + this.DATAPLANE_API_ENDPOINT + '/metadata/' + asset_id + '/WebToVTTCaptions');
            console.log("Data:");
            console.log((data));
            console.log("Response: " + res.status);
          }
          this.vttcaptions = [];
          this.num_caption_tracks = res.data.results.CaptionsCollection.length;
          // now get signed urls that can be used to download the vtt files from s3
          this.asyncForEach(res.data.results.CaptionsCollection, async(item) => {
            const bucket = item.Results.S3Bucket;
            const key = item.Results.S3Key;
            // get the signed url
            await fetch(this.DATAPLANE_API_ENDPOINT + '/download', {
              method: 'POST',
              mode: 'cors',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': token
              },
              body: JSON.stringify({"S3Bucket": bucket, "S3Key": key})
            }).then(data => {
              data.text().then((data) => {
                // record the signed urls in an array
                this.vttcaptions.push({'src': data, 'lang': item.LanguageCode, 'label': item.LanguageCode});
              }).catch(err => console.error(err));
            })
          }).then(() => {
            // now that we have all the signed urls to download vtt files,
            // update the captions in the video player for the currently selected
            // language. This will make sure the video player reflects any edits
            // that the user may have saved by clicking the Save Edits button.
            if (this.selected_lang_code !== "") {
              // hide all the captions in the video player
              for (let i = 0; i < this.player.textTracks().length; i++) {
                let track = this.player.textTracks()[i];
                track.mode = "disabled";
              }
              // get the src for that language's vtt file
              let old_track = this.player.textTracks()["tracks_"].filter(x => (x.language == this.selected_lang_code))[0]
              // create properties for a new track
              let new_track = {}
              new_track.label = old_track.label
              new_track.language = old_track.language
              new_track.kind = old_track.kind
              new_track.src = this.vtt_url
              // show the new caption in the video player
              new_track.mode = "showing"
              // remove the old track for that vtt
              this.player.removeRemoteTextTrack(old_track)
              // add a new text track for that vtt
              const manualCleanup = false
              // manualCleanup is needed in order to avoid a warning
              this.player.addRemoteTextTrack(new_track, manualCleanup)
            }
          })

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
    getPollyAudioTranscripts: async function () {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const asset_id = this.$route.params.asset_id;

      fetch(this.DATAPLANE_API_ENDPOINT + '/metadata/' + asset_id + '/PollyWebCaptions', {
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
          res.data.results.CaptionsCollection.forEach(item => {
            // TODO: map the language code to a language label
            if (item.PollyStatus != "not supported") {
              const bucket = item.PollyAudio.S3Bucket;
              const key = item.PollyAudio.S3Key;
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
                  captions_collection.push({'src': data, 'lang': item.TargetLanguageCode, 'label': item.TargetLanguageCode});
                }).catch(err => console.error(err));
              });
            }
          });
          this.pollyaudiotranscripts = captions_collection
        })
      });
    },
    downloadAudioFile() {
      const blob = new Blob([this.pollyaudio_url], {type: 'audio/mpeg', autoplay:'0', autostart:'false', endings:'native'});
      const e = document.createEvent('MouseEvents'),
        a = document.createElement('a');
      a.download = "audiofile.mp3";
      a.href = window.URL.createObjectURL(blob);
      a.dataset.downloadurl = ['audio/mpeg', a.download, a.href].join(':');
      e.initEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
      a.dispatchEvent(e);
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
              // get the list of languages to show the user
              this.getLanguageList();
              // get workflow config, needed for edit captions button
              this.getWorkflowConfig(token);
            }
          )
        }
      )
    },
    getWorkflowStatus: async function() {
      // This function gets the workflow status. If its in a running state
      // then we temporarily disable the ability for users to edit
      // translations in the GUI.
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
              const new_workflow_status = res.data[0].Status
              if (this.workflow_status !== 'Complete'
                && new_workflow_status === 'Complete') {
                this.getVttCaptions()
              }
              this.workflow_status = new_workflow_status
            }
          )
        }
      )
    },
    getWorkflowConfig: async function(token) {
      // This function gets the workflow configuration that is used
      // to update the saved vtt and srt caption files after a user saves
      // translation edits.
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
    disableUpstreamStages()  {
      // This function disables all the operators in stages above TranslateStage2,
      // so all that's left are the operators that update vtt and srt files.
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
      // This loop starts at the first stage and
      // goes until the staged named "End"
      while (end == false) {
        // If the current stage is End then end the loop.
        if ("End" in stage && stage["End"] == true){
          end = true
        }
        // If the current stage is CaptionFileStage2 then end the loop.
        else if (stage_name == "CaptionFileStage2") {
          end = true
        }
        // For all other stages disable all the operators in the stage
        else {
          // Disable all the operators in the stage
          for (const operator in data["Configuration"][stage_name]){
            data["Configuration"][stage_name][operator]["Enabled"] = false
          }
          // Now look at the next stage in the workflow
          stage_name = stage["Next"]
          stage = workflow["Stages"][stage_name]
        }
      }

      return data

    },
    rerunWorkflow: async function (token) {
      // This function reruns CaptionFileStage2 in order to
      // regenerate VTT and SRT files.
      let data = this.disableUpstreamStages();

      data["Configuration"]["TranslateStage2"]["TranslateWebCaptions"].MediaType = "MetadataOnly";

      // execute workflow to update VTT and SRT files
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
          this.pollWorkflowStatus()
          if (res.status !== 200) {
            console.log("ERROR: Failed to start workflow.");
            console.log(res.data.Code);
            console.log(res.data.Message);
            console.log("URL: " + this.WORKFLOW_API_ENDPOINT + 'workflow/execution');
            console.log("Data:");
            console.log(JSON.stringify(data));
            console.log((data));
            console.log("Response: " + response.status);
          }
        })
      )
    },
    saveCaptions: async function (token) {
      clearInterval(this.workflow_status_polling)
      this.workflow_status = "Started"
      // This function saves translation edits to the dataplane
      this.$refs['save-modal'].hide()
      this.isSaving=true;
      if (!token) {
        token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
      }
      const operator_name = "WebCaptions_"+this.selected_lang_code
      const web_captions = {"WebCaptions": this.webCaptions}
      let data='{"OperatorName": "' + operator_name + '", "Results": ' + JSON.stringify(web_captions) + ', "WorkflowId": "' + this.workflow_id + '"}'
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
            console.log("Saving translation for " + this.selected_lang_code)
            this.rerunWorkflow(token);
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
    getWebCaptions: async function () {
      // This functions gets paginated web caption data
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        return data.getIdToken().getJwtToken();
      });
      const operator_name = "WebCaptions_"+this.selected_lang_code
      let cursor=''
      let url = this.DATAPLANE_API_ENDPOINT + '/metadata/' + this.asset_id + '/' + operator_name
      this.webCaptions = []
      await this.getWebCaptionPages(token, url, cursor)
      // switch the video player to show the selected language
      // by first disabling all the text tracks, like this:
      for (let i = 0; i < this.player.textTracks().length; i++) {
        let track = this.player.textTracks()[i];
        track.mode = "disabled";
      }
      // then showing the text track for the selected language
      this.player.textTracks()["tracks_"].filter(x => (x.language == this.selected_lang_code))[0].mode = "showing"
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
      // clearInterval(this.workflow_status_polling)
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

