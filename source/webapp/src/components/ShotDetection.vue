<template>
  <div>
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
        :items="elasticsearch_data"
        :fields="fields"
        :sort-by="sortBy"
      >
        <template v-slot:cell(Index)="data">
          <b-button variant="link" @click="setPlayerTime(data.item.StartTimestamp)"> 
            {{ data.item.Index }}
          </b-button>
        </template>
      </b-table>
      <b-button
        type="button"
        @click="saveFile()"
      >
        Download Data
      </b-button>
    </div>
  </div>
</template>

<script>
  import Loading from '@/components/Loading.vue'
  import { mapState } from 'vuex'
  export default {
    name: "ShotDetection",
    components: {
      Loading
    },
    props: {
      mediaType: {
        type: String,
        default: ""
      },
    },
    data() {
      return {
        sortBy: 'Index',
        fields: [
          {
            'Index': {
              label: 'Shot Number',
              sortable: true
            }
          },
          {
            'StartTimecodeSMPTE': {
              label: 'Start',
              sortable: false
            }
          },
          {
            'EndTimecodeSMPTE': { 
              label: 'End',
              sortable: false 
              }
          },
          {
            'DurationSMPTE': { 
              label: 'Duration',
              sortable: true
              }
          },
          { key: 'Confidence', sortable: true }
      ],
        elasticsearch_data: [],
        isBusy: false,
        operator: 'shot_detection',
      }
    },
    computed: {
      ...mapState(['player'])
    },
    deactivated: function () {
      console.log('deactivated component:', this.operator);
    },
    activated: function () {
      console.log('activated component:', this.operator)
      this.fetchAssetData();
    },
    beforeDestroy: function () {
      this.elasticsearch_data = [];
    },
    methods: {
      setPlayerTime(milliseconds) {
        let seconds = milliseconds / 1000
        let playerTime = Math.ceil(seconds)
        this.player.currentTime(playerTime)
      },
      saveFile() {
        const elasticsearch_data = JSON.stringify(this.elasticsearch_data);
        const blob = new Blob([elasticsearch_data], {type: 'text/plain'});
        const e = document.createEvent('MouseEvents'),
          a = document.createElement('a');
        a.download = "data.json";
        a.href = window.URL.createObjectURL(blob);
        a.dataset.downloadurl = ['text/json', a.download, a.href].join(':');
        e.initEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
        a.dispatchEvent(e);
      },
      async fetchAssetData () {
          let query = 'AssetId:'+this.$route.params.asset_id+' Operator:'+this.operator;
          let apiName = 'mieElasticsearch';
          let path = '/_search';
          let apiParams = {
            headers: {'Content-Type': 'application/json'},
            queryStringParameters: {'q': query, 'default_operator': 'AND', 'size': 10000}
          };
          let response = await this.$Amplify.API.get(apiName, path, apiParams);
          console.log(response)
          if (!response) {
            this.showElasticSearchAlert = true
          }
          else {
            let es_data = [];
            let result = await response;
            let data = result.hits.hits;
            if (data.length === 0 && this.Confidence > 55) {
                this.lowerConfidence = true;
                this.lowerConfidenceMessage = 'Try lowering confidence threshold'
            }
            else {
              this.lowerConfidence = false;
              for (let i = 0, len = data.length; i < len; i++) {
                es_data.push(data[i]._source)
              }
            }
            this.elasticsearch_data = JSON.parse(JSON.stringify(es_data));
            this.isBusy = false
        }
      }
    }
  }
</script>
