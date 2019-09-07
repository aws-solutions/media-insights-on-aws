<template>
  <b-container fluid>
    <b-col>
      <b-row align-h="center" class="my-1">
        <div class="wrapper">
          Confidence Threshold<br>
          <input @click="updateConfidence" type="range" value="90" min="55" max="99" step="1">
          {{ Confidence }}%<br>
        </div>
      </b-row>
        <div v-if="this.isBusy" class="wrapper">
          <Loading/>
        </div>
      <b-row align-h="center" class="my-1">
        <div class="wrapper">
          <br>
          <template v-for="label in sorted_unique_labels">
            <b-button variant="outline-secondary" v-b-tooltip.hover :title=label[1] v-on:click="updateMarkers(label[0])" size="sm" pill>{{ label[0] }}</b-button> &nbsp;
          </template>
        </div>
      </b-row>

      <b-row align-h="center" class="my-1">
          <div v-if="this.isBusy === false" class="wrapper">
            <br><p class="text-muted">({{ count_labels }} identified objects, {{ count_distinct_labels }} unique)</p>
          </div>
      </b-row>
    </b-col>
    <b-button type="button" v-on:click="saveFile()">Download Data</b-button>
  </b-container>
</template>

<script>
  import { mapState } from 'vuex'
  import Loading from '@/components/Loading.vue'

  export default {
    name: "Celebrities",
    components: {
      Loading
    },
    data() {
      return {
        high_confidence_data: [],
        elasticsearch_data: [],
        count_distinct_labels: 0,
        count_labels: 0,
        isBusy: false,
        operator: 'celebrity_detection'
      }
    },
    methods: {
      saveFile() {
        const elasticsearch_data = this.elasticsearch_data;
        const blob = new Blob([elasticsearch_data], {type: 'text/plain'});
        const e = document.createEvent('MouseEvents'),
          a = document.createElement('a');
        a.download = "data.json";
        a.href = window.URL.createObjectURL(blob);
        a.dataset.downloadurl = ['text/json', a.download, a.href].join(':');
        e.initEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
        a.dispatchEvent(e);
      },
      updateConfidence (event) {
        this.isBusy = !this.isBusy
        this.$store.commit('updateConfidence', event.target.value);
        this.player.markers.removeAll();
        this.fetchAssetData()
      },
      updateMarkers (label) {
        // this function updates markers in the video player and is called when someone clicks on a label button
        var markers = [];
        var es_data = this.elasticsearch_data
        es_data.forEach(function (record) {
          if (record.Name === label) {
            markers.push({'time': record.Timestamp/1000, 'text': record.Name, 'overlayText': record.Name})
          }
        });
        this.player.markers.removeAll();
        this.player.markers.add(markers);
      },
      fetchAssetData () {
        fetch(process.env.VUE_APP_ELASTICSEARCH_ENDPOINT+'/_search?q=AssetId:'+this.$route.params.asset_id+' Confidence:>'+this.Confidence+' Operator:'+this.operator+'&default_operator=AND&size=10000', {
          method: 'get'
        }).then(response =>
          response.json().then(data => ({
              data: data,
              status: response.status
            })
          ).then(res => {
            var es_data = [];
            res.data.hits.hits.forEach(function (item) {
              es_data.push(item._source)
            });
            this.elasticsearch_data = JSON.parse(JSON.stringify( es_data ))
            this.isBusy = false
          })
        );
      }
    },
    computed: {
      ...mapState(['Confidence', 'player']),
      sorted_unique_labels() {
        // this.fetchAssetData()
        // This function sorts and counts unique labels for mouse over events on label buttons
        var es_data = this.elasticsearch_data;
        const unique_labels = new Map();
        // sort and count unique labels for label mouse over events
        es_data.forEach(function (record) {
          unique_labels.set(record.Name, unique_labels.get(record.Name) ? unique_labels.get(record.Name) + 1 : 1)
        });
        var sorted_unique_labels = new Map([...unique_labels.entries()].slice().sort((a, b) => b[1] - a[1]))
        // If Elasticsearch returned undefined labels then delete them:
        sorted_unique_labels.delete(undefined);
        //console.log(es_data.length + ' labels, ' + sorted_unique_labels.size + ' unique');
        this.count_distinct_labels = sorted_unique_labels.size;
        this.count_labels = es_data.length;
        return sorted_unique_labels
      }
    },
    deactivated: function () {
      console.log('deactivated component:', this.operator)
    },
    activated: function () {
      console.log('activated component:', this.operator)
      this.fetchAssetData();
    },
    beforeDestroy: function () {
        this.high_confidence_data = [],
        this.elasticsearch_data = [],
        this.count_distinct_labels = 0,
        this.count_labels = 0
    }
  }
</script>
