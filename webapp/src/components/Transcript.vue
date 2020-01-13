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
      {{ transcript }}
    </div>
  </div>
</template>

<script>
export default {
  name: "Transcript",
  data() {
    return {
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
