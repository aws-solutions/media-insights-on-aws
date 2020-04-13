<template>
  <div>
    <div v-if="noTranscript === true">
      No transcript found for this asset
    </div>
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
      <b-table thead-class="hidden_header" fixed responsive="sm" :items="webCaptions" :fields="webCaptions_fields">
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
          <b-form-textarea class="custom-text-field .form-control-sm" max-rows="8" v-model="data.item.caption"/>
              </b-col>
              <b-col>
                <span style="position:absolute; top: 3px">
                  <b-icon-x-circle color="lightgrey"></b-icon-x-circle><br><br>
                </span>
                <span style="position:absolute; bottom: 0px">
                  <b-icon-plus-square color="lightgrey"></b-icon-plus-square>
                </span>
              </b-col>
            </b-row>
          </b-container>
        </template>
      </b-table>
      </div>
    </div>
  </div>
</template>

<script>
import webcaptions_file from '../json/WebCaptions_en.json'

export default {
  name: "Transcript",
  data() {
    return {
      webCaptions: webcaptions_file,
      webCaptions_fields: ['timeslot', 'caption'],
      transcript: "",
      isBusy: false,
      operator: "transcript",
      noTranscript: false
    }
  },
  computed: {
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
    this.fetchAssetData();
  },
  beforeDestroy: function () {
      this.transcript = ''
  },
  methods: {
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
  .custom-text-field {
    border: 0;
  }
</style>
