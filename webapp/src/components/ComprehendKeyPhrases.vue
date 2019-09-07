<template>
  <div>
    <div class="wrapper">
      Confidence Threshold<br>
      <input @click="updateConfidence" type="range" value="90" min="55" max="99" step="1">
      {{ Confidence }}%<br>
    </div>
    <div v-if="this.isBusy" class="wrapper">
        <Loading />
    </div>
    <div v-else class="wrapper">
      <b-table responsive fixed :items="key_phrases" :fields="fields" :sort-by="sortBy"></b-table>
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
  methods: {
    updateConfidence (event) {
        this.isBusy = true
        this.$store.commit('updateConfidence', event.target.value);
        this.fetchAssetData()
    },
    fetchAssetData () {
      const vm = this;
      fetch(process.env.VUE_APP_ELASTICSEARCH_ENDPOINT+'/_search?q=AssetId:'+this.$route.params.asset_id+' Confidence:>'+this.Confidence+' _index:miekey_phrases&default_operator=AND&size=100', {
        method: 'get'
      }).then(response =>
        response.json().then(data => ({
            data: data,
            status: response.status
          })
        ).then(res => {
          res.data.hits.hits.forEach(function (item) {
            vm.key_phrases.push({ "PhraseText": item._source.PhraseText, "Confidence": item._source.Confidence, "BeginOffset": item._source.BeginOffset, "EndOffset": item._source.EndOffset})
          });
          vm.isBusy = false
        })
      );
    }
  },
  computed: {
      ...mapState(['Confidence', 'player']),
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
    }
}
</script>
