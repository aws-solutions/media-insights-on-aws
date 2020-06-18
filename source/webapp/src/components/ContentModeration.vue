<template>
  <b-container fluid>
    <b-col>
      <b-row
        align-h="center"
        class="my-1"
      >
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
      </b-row>
      <div v-if="lowerConfidence === true">
        {{ lowerConfidenceMessage }}
      </div>
      <div
        v-if="isBusy"
        class="wrapper"
      >
        <Loading />
      </div>
      <b-row
        align-h="center"
        class="my-1"
      >
        <div class="wrapper">
          <br>
          <template v-for="label in sorted_unique_labels">
            <!-- Show lighter button outline since content moderation never provides bounding boxes -->
            <b-button
              v-b-tooltip.hover
              variant="outline-secondary"
              :title="label[1]"
              size="sm"
              pill
              @click="updateMarkers(label[0])"
            >
              {{ label[0] }}
            </b-button> &nbsp;
          </template>
        </div>
      </b-row>

      <b-row
        align-h="center"
        class="my-1"
      >
        <div
          v-if="isBusy === false"
          class="wrapper"
        >
          <br><p class="text-muted">
            ({{ count_labels }} identified objects, {{ count_distinct_labels }} unique)
          </p>
        </div>
      </b-row>
    </b-col>
    <b-button
      type="button"
      @click="saveFile()"
    >
      Download Data
    </b-button>
  </b-container>
</template>

<script>
  import { mapState } from 'vuex'
  import Loading from '@/components/Loading.vue'

  export default {
    name: "ContentModeration",
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
        Confidence: 90,
        high_confidence_data: [],
        elasticsearch_data: [],
        count_distinct_labels: 0,
        count_labels: 0,
        isBusy: false,
        operator: 'content_moderation',
        timeseries: new Map(),
        selectedLabel: '',
        lowerConfidence: false,
        lowerConfidenceMessage: 'Try lowering confidence threshold'
      }
    },
    computed: {
      ...mapState(['player']),
      sorted_unique_labels() {
        // This function sorts and counts unique labels for mouse over events on label buttons
        const es_data = this.elasticsearch_data;
        const unique_labels = new Map();
        // sort and count unique labels for label mouse over events
        es_data.forEach(function (record) {
          unique_labels.set(record.Name, unique_labels.get(record.Name) ? unique_labels.get(record.Name) + 1 : 1)
        });
        const sorted_unique_labels = new Map([...unique_labels.entries()].slice().sort((a, b) => b[1] - a[1]));
        // If Elasticsearch returned undefined labels then delete them:
        sorted_unique_labels.delete(undefined);
        this.countLabels(sorted_unique_labels.size, es_data.length);
        return sorted_unique_labels
      }
    },
    watch: {
      // These watches update the line chart
      selectedLabel: function() {
        this.chartData();
      },
      elasticsearch_data: function() {
        this.chartData();
      },
    },
    deactivated: function () {
      console.log('deactivated component:', this.operator);
      this.selectedLabel = '';
    },
    activated: function () {
      console.log('activated component:', this.operator);
      this.fetchAssetData();
    },
    beforeDestroy: function () {
      this.high_confidence_data = [];
      this.elasticsearch_data = [];
      this.count_distinct_labels = 0;
      this.count_labels = 0;
    },
    methods: {
      countLabels(unique_count, total_count) {
        this.count_distinct_labels = unique_count;
        this.count_labels = total_count;
      },
      saveFile() {
        const elasticsearch_data = this.elasticsearch_data;
        const blob = new Blob([JSON.stringify(elasticsearch_data)], {type: 'text/plain'});
        const e = document.createEvent('MouseEvents'),
          a = document.createElement('a');
        a.download = "data.json";
        a.href = window.URL.createObjectURL(blob);
        a.dataset.downloadurl = ['text/json', a.download, a.href].join(':');
        e.initEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
        a.dispatchEvent(e);
      },
      updateConfidence (event) {
        this.isBusy = !this.isBusy;
        this.Confidence = event.target.value;
        // TODO: move image processing to a separate component
        if (this.mediaType === "video") {
          // redraw markers on video timeline
          this.player.markers.removeAll();
        }
        this.fetchAssetData()
      },
      // updateMarkers updates markers in the video player and is called when someone clicks on a label button
      updateMarkers (label) {
        if (this.selectedLabel === label) {
          // keep the canvas clear canvas if user clicked the label button a second consecutive time
          this.selectedLabel = "";
          return
        }
        this.selectedLabel = label;
        let markers = [];
        const es_data = this.elasticsearch_data;
        es_data.forEach(function (record) {
          if (record.Name === label) {
            markers.push({'time': record.Timestamp/1000, 'text': record.Name, 'overlayText': record.Name})
          }
        });
        // TODO: move image processing to a separate component
        if (this.mediaType === "video") {
          // redraw markers on video timeline
          this.player.markers.removeAll();
          this.player.markers.add(markers);
        }
      },
      async fetchAssetData () {
          let query = 'AssetId:'+this.$route.params.asset_id+' Confidence:>'+this.Confidence+' Operator:'+this.operator;
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
            let es_data = [];
            let result = await response;
            let data = result.hits.hits;
            let dataLength = data.length;
            if (dataLength === 0 && this.Confidence > 55)  {
              this.lowerConfidence = true;
              this.lowerConfidenceMessage = 'Try lowering confidence threshold'
            }
            else {
              this.lowerConfidence = false;
              for (let i = 0, len = dataLength; i < len; i++) {
                es_data.push(data[i]._source)
              }
            }
            this.elasticsearch_data = JSON.parse(JSON.stringify(es_data));
            this.isBusy = false
        }
      },
      chartData() {
        let timeseries = new Map();
        function saveTimestamp (millisecond) {
          if (timeseries.has(millisecond)) {
            timeseries.set(millisecond, {"x": millisecond, "y": timeseries.get(millisecond).y + 1})
          } else {
            timeseries.set(millisecond, {"x": millisecond, "y":1})
          }
        }
        const es_data = this.elasticsearch_data;
        es_data.forEach( function(record) {
          // Define timestamp with millisecond resolution
          const millisecond = Math.round(record.Timestamp);
          if (this.selectedLabel) {
            // If label is defined, then enumerate timestamps for that label
            if (record.Name === this.selectedLabel) {
              saveTimestamp(millisecond);
            }
          } else {
            // No label has been selected, so enumerate timestamps for all label names.
            saveTimestamp(millisecond);
          }
        }.bind(this));
        //sort the timeseries map by its millisecond key
        const ordered_timeseries = new Map([...timeseries.entries()].slice().sort((a, b) => a[0] - b[0]));
        const chartTuples = Array.from(ordered_timeseries.values());
        this.$store.commit('updateTimeseries', chartTuples);
        this.$store.commit('updateSelectedLabel', this.selectedLabel);
      },
    }
  }
</script>
