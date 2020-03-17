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
          <template v-for="detectedWords in sorted_unique_word_detections">
            <template v-if="boxes_available.includes(detectedWords[0])">
              <!-- Show darker button outline if bounding boxes are available for the detected text -->
              <b-button
                v-b-tooltip.hover
                variant="outline-dark"
                :title="detectedWords[1]"
                size="sm"
                pill
                @click="updateMarkers(detectedWords[0])"
              >
                {{ detectedWords[0]+"*" }}
              </b-button> &nbsp;
            </template>
            <template v-else>
              <b-button
                v-b-tooltip.hover
                variant="outline-secondary"
                :title="detectedWords[1]"
                size="sm"
                pill
                @click="updateMarkers(detectedWords[0])"
              >
                {{ detectedWords[0] }}
              </b-button> &nbsp;
            </template>
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
          <p class="text-muted">
            ({{ count_words }} identified text objects, {{ count_distinct_words }} unique)
          </p>
          <hr>
          <p class="text-muted">
            * Indicates bounding boxes are available.
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
  import Loading from '@/components/Loading.vue'
  import { mapState } from 'vuex'
  // TODO: Think about how to handle "LINE" detection types, maybe another component? or a drop down to filter words / lines
  export default {
    name: "TextDetection",
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
        boxes_available: [],
        count_distinct_words: 0,
        count_words: 0,
        //count_distinct_lines: 0,
        //count_lines: 0,
        isBusy: false,
        operator: 'textDetection',
        canvasRefreshInterval: undefined,
        timeseries: new Map(),
        selectedWord: '',
        lowerConfidence: false,
        lowerConfidenceMessage: 'Try lowering confidence threshold',
      }
    },
    computed: {
      ...mapState(['player']),
      sorted_unique_word_detections() {
        // This function sorts and counts unique words for mouse over events on buttons
        const es_data = this.elasticsearch_data;
        console.log(es_data)
        const unique_words = new Map();
        //const unique_lines = new Map();
        // sort and count unique words for mouse over events
        es_data.forEach(function (record) {
          if (record.Type == 'WORD') {
            unique_words.set(record.DetectedText, unique_words.get(record.DetectedText) ? unique_words.get(record.DetectedText) + 1 : 1);
          }
          // if (record.TextType == 'LINE') {
          //   unique_lines.set(record.DetectedText, unique_lines.get(record.DetectedText) ? unique_lines.get(record.DetectedText) + 1 : 1);
          // }
          if (record.BoundingBox) {
            // Save this word detection to a list of words that have bounding boxes
            this.saveBoxedDetectedText(record.DetectedText)
          }
        }.bind(this));
        const sorted_unique_words = new Map([...unique_words.entries()].slice().sort((a, b) => b[1] - a[1]));
        //const sorted_unique_lines = new Map([...unique_lines.entries()].slice().sort((a, b) => b[1] - a[1]));
        // If Elasticsearch returned undefined words then delete them:
        sorted_unique_words.delete(undefined);
        //sorted_unique_lines.delete(undefined);
        this.countDetectedWords(sorted_unique_words.size, es_data.length);
        //this.countDetectedLines(sorted_unique_lines.size, es_data.length);
        console.log(sorted_unique_words)
        return sorted_unique_words
      },
    },
    watch: {
      // These watches update the line chart
      selectedWord: function() {
        this.chartData();
      },
      elasticsearch_data: function() {
        this.chartData();
      },
    },
    deactivated: function () {
      this.boxes_available = [];
      this.selectedWord = '';
      clearInterval(this.canvasRefreshInterval);
      const canvas = document.getElementById('canvas');
      let ctx;
      if (canvas) ctx = canvas.getContext('2d');
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    },
    activated: function () {
      this.fetchAssetData();
    },
    beforeDestroy: function () {
      this.high_confidence_data = [];
      this.elasticsearch_data = [];
      this.count_distinct_words = 0;
      this.count_words = 0;
      clearInterval(this.canvasRefreshInterval);
    },
    methods: {
      saveBoxedDetectedText(detectedText){
        if (!this.boxes_available.includes(detectedText)) {
          this.boxes_available.push(detectedText);
        }
      },
      countDetectedWords(uniqueWordCount, totalWordCount) {
        this.count_distinct_words = uniqueWordCount;
        this.count_words = totalWordCount;
        // this.count_distinct_lines = uniqueLineCount;
        // this.count_lines = totalLineCount;
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
      updateConfidence (event) {
        this.isBusy = true;
        this.Confidence = event.target.value;
        if (this.mediaType === "video") {
          // redraw markers on video timeline
          this.player.markers.removeAll();
        }
        this.fetchAssetData()
      },
      // updateMarkers updates markers in the video player and is called when someone clicks on a word button
      updateMarkers (word) {
        // clear canvas for redrawing
        this.boxes_available = [];
        clearInterval(this.canvasRefreshInterval);
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = "red";  
        ctx.font = "15px Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = "red";
        if (this.selectedWord === word) {
          // keep the canvas clear canvas if user clicked the word button a second consecutive time
          this.selectedWord = "";
          return
        }
        this.selectedWord = word;        // initialize lists of boxes and markers to be drawn
        const boxMap = new Map();
        const markers = [];
        const es_data = this.elasticsearch_data;
        es_data.forEach( function(record) {
          if (record.DetectedText === word) {
            // Save word text overlaying on video timeline
            markers.push({'time': record.Timestamp/1000, 'text': record.DetectedText, 'overlayText': record.DetectedText});
            // Save bounding box info if it exists
            if (record.BoundingBox) {
                const item = record;
                // TODO: move image processing to a separate component
                if (this.mediaType === "image") {
                  // use timestamp to index boxes in the boxMap collection
                  const boxinfo = {
                    'name': item.DetectedText,
                    'confidence': (item.Confidence * 1).toFixed(2),
                    'x': item.BoundingBox.Left * canvas.width,
                    'y': item.BoundingBox.Top * canvas.height,
                    'width': item.BoundingBox.Width * canvas.width,
                    'height': item.BoundingBox.Height * canvas.height
                  };
                  boxMap.set(i, [boxinfo])
                } else {
                  // Use time resolution of 0.1 second
                  const timestamp = Math.round(record.Timestamp/100);
                  const boxinfo = {'timestamp':Math.ceil(record.Timestamp/100), 'name':record.DetectedText, 'confidence':(record.Confidence * 1).toFixed(2), 'x':item.BoundingBox.Left*canvas.width, 'y':item.BoundingBox.Top*canvas.height, 'width':item.BoundingBox.Width*canvas.width, 'height':item.BoundingBox.Height*canvas.height};
                  // If there are multiple bounding boxes for this instance at this
                  // timestamp, then save them together in an array.
                  if (boxMap.has(timestamp)) {
                    boxMap.get(timestamp).push(boxinfo)
                  } else {
                    boxMap.set(timestamp, [boxinfo])
                  }
                }
            }
          }
        }.bind(this));
        if (boxMap.size > 0) {
          this.drawBoxes(boxMap);
        }
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
      },
      drawBoxes: function(boxMap) {
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        // TODO: move image processing to a separate component
        if (this.mediaType === "image") {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.beginPath();
          ctx.strokeStyle = "red";
          ctx.font = "15px Arial";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillStyle = "red";
          // For each box instance...
          boxMap.forEach( i => {
            const drawMe = i[0];
            if (drawMe) {
              ctx.rect(drawMe.x, drawMe.y, drawMe.width, drawMe.height);
              // Draw object name and confidence score
              ctx.fillText(drawMe.name + " (" + drawMe.confidence + "%)", (drawMe.x + drawMe.width / 2), drawMe.y - 10);
              ctx.stroke();
            }
          });
          // now return so we avoid rendering any of the video related components below
          return
        }
        // If user just clicked a new word...
        if (this.canvasRefreshInterval !== undefined) {
          // ...then reset the old canvas refresh interval.
          clearInterval(this.canvasRefreshInterval)
        }
        // Look for and draw bounding boxes every 100ms
        const interval_ms = 100;
        const erase_on_iteration = 2;
        let i = 0;
        this.canvasRefreshInterval = setInterval(function () {
          i++;
          // erase old bounding boxes
          if (!this.player.paused() && i % erase_on_iteration === 0) {
            i=0;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.beginPath();
            ctx.strokeStyle = "red";
            ctx.font = "15px Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "red";
          }
          // Get current player timestamp to the nearest 1/10th second
          const player_timestamp = Math.round(this.player.currentTime()*10.0);
          // If we have a box for the player's timestamp...
          if (boxMap.has(player_timestamp)) {
            i=0;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.beginPath();
            ctx.strokeStyle = "red";
            ctx.font = "15px Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "red";
            // ...then get a list of box instances
            const instance_list = (boxMap.get(player_timestamp)).map( item => item.instance).filter((v, i, a) => a.indexOf(v) === i);
            // For each box instance...
            instance_list.forEach( i => {
              // ...get all of the boxes belonging to this instance
              // at the current timestamp.
              const boxes = boxMap.get(player_timestamp).filter(box => box.instance === i);
              boxes.forEach (drawMe => {
                if (drawMe) {
                  ctx.rect(drawMe.x, drawMe.y, drawMe.width, drawMe.height);
                  // Draw object name and confidence score
                  ctx.fillText(drawMe.name + " (" + drawMe.confidence + "%)", (drawMe.x + drawMe.width / 2), drawMe.y - 10);
                }
              })
            });
            ctx.stroke();
          }
        }.bind(this), interval_ms);
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
          if (this.selectedWord) {
            // If word is defined, then enumerate timestamps for that word
            if (record.DetectedText === this.selectedWord) {
                  saveTimestamp(millisecond);
            }
          } 
          else {
            // No word has been selected, so enumerate timestamps for all word names.
            // Iterate through bounding boxes if present.
            saveTimestamp(millisecond);
          }
        }.bind(this));
        //sort the timeseries map by its millisecond key
        const ordered_timeseries = new Map([...timeseries.entries()].slice().sort((a, b) => a[0] - b[0]));
        const chartTuples = Array.from(ordered_timeseries.values());
        this.$store.commit('updateTimeseries', chartTuples);
        this.$store.commit('updateSelectedLabel', this.selectedWord);
      },
    }
  }
</script>
