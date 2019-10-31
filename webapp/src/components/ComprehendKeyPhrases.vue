<template>
  <div>
    <div class="wrapper">
      Confidence Threshold<br>
      <input
        type="range"
        value="90"
        min="55"
        max="99"
        step="1"
        @click="updateConfidence"
      >
      {{ Confidence }}%<br>
    </div>
    <div
      v-if="isBusy"
      class="wrapper"
    >
      <Loading />
    </div>
    <div
      v-else
      class="wrapper"
    >
      <b-table
        responsive
        fixed
        :items="key_phrases"
        :fields="fields"
        :sort-by="sortBy"
      >
        <template v-slot:cell(Confidence)="data">
          {{ (data.item.Confidence * 1).toFixed(2) }}
        </template>
      </b-table>
    </div>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue'
import { mapState } from 'vuex'

export default {
  name: "KeyPhrases",
  components: {
    Loading
  },
  data() {
    return {
      Confidence: 90,
      sortBy: "BeginOffset",
      fields: [
        { key: 'PhraseText', sortable: false },
        { key: 'Confidence', sortable: true },
        { key: 'BeginOffset', sortable: true },
        { key: 'EndOffset', sortable: true },
      ],
      key_phrases: [],
      isBusy: false,
      operator: "key_phrases"
    }
  },
  computed: {
    ...mapState(['player']),
  },
  deactivated: function () {
    console.log('deactivated component:', this.operator)
    // clearing this value after every deactivation so we dont carry this huge amount of data in memory
    this.key_phrases = []
  },
  activated: function () {
    console.log('activated component:', this.operator)
    this.fetchAssetData();
  },
  beforeDestroy: function () {
    this.key_phrases = []
  },
  methods: {
    updateConfidence (event) {
        this.isBusy = true;
        this.key_phrases = [];
        this.Confidence = event.target.value;
        this.fetchAssetData()
    },
    async fetchAssetData () {
      let query = 'AssetId:'+this.$route.params.asset_id+' Confidence:>'+this.Confidence+' _index:miekey_phrases'
      let apiName = 'mieElasticsearch';
      let path = '/_search';
      let apiParams = {
        headers: {'Content-Type': 'application/json'},
        queryStringParameters: {'q': query, 'default_operator': 'AND', 'size': 10000}
      }
      let response = await this.$Amplify.API.get(apiName, path, apiParams)
      if (!response) {
        this.showElasticSearchAlert = true
      }
      else {
        let result = await response
        let data = result.hits.hits
        for (var i = 0, len = data.length; i < len; i++) {
          this.key_phrases.push({ "PhraseText": data[i]._source.PhraseText, "Confidence": data[i]._source.Confidence, "BeginOffset": data[i]._source.BeginOffset, "EndOffset": data[i]._source.EndOffset})
        }
        this.isBusy = false
      }
    }
  }
}
</script>
