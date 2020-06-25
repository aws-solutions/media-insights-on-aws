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
            value="70"
            min="1"
            max="99"
            step="1"
            @click="updateConfidence"
          >
          {{ Confidence }}%<br>
        </div>
      </b-row>
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
            <template v-if="points_available.includes(label[0])">
              <b-button
                v-b-tooltip.hover
                variant="outline-dark"
                :title="label[1]"
                size="sm"
                pill
                @click="updateMarkers(label[0])"
              >
                {{ label[0]+"*" }}
              </b-button> &nbsp;
            </template>
            <template v-else>
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
          <hr>
          <p class="text-muted">
            * Indicates pose is available.
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
  export default {
    name: "Pose",
    components: {
      Loading
    },
    data() {
      return {
        Confidence: 70,
        high_confidence_data: [],
        elasticsearch_data: [],
        count_distinct_labels: 0,
        count_labels: 0,
        isBusy: false,
        operator: 'poseInference',
        canvasRefreshInterval: undefined,
        timeseries: new Map(),
        selectedLabel: '',
        points_available: []
      }
    },
    computed: {
      ...mapState(['player']),
      sorted_unique_labels() {
        // This function sorts and counts unique labels for mouse over events on label buttons
        var es_data = this.elasticsearch_data;
        const unique_labels = new Map();
        // sort and count unique labels for label mouse over events
        es_data.forEach(function (record) {
          record.Name = "Pose"
          unique_labels.set(record.Name, unique_labels.get(record.Name) ? unique_labels.get(record.Name) + 1 : 1)
          if (record.points) {
            // Save this label name to a list of labels that have bounding points
            this.savePointsLabel(record.Name)
          }
        }.bind(this));
        var sorted_unique_labels = new Map([...unique_labels.entries()].slice().sort((a, b) => b[1] - a[1]))
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
      console.log('activated component:', this.operator);
      this.points_available = [];
      this.selectedLabel = '';
      clearInterval(this.canvasRefreshInterval);
      var canvas = document.getElementById('canvas');
      if (canvas) var ctx = canvas.getContext('2d');
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
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
      savePointsLabel(label_name) {
        if (!this.points_available.includes(label_name)) {
          this.points_available.push(label_name);
        }
      },
      countLabels(unique_count, total_count) {
        this.count_distinct_labels = unique_count;
        this.count_labels = total_count;
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
        this.isBusy = true
        this.Confidence = event.target.value;
        this.player.markers.removeAll();
        this.fetchAssetData()
      },
      updateMarkers (label) {
        // this function updates markers in the video player and is called when someone clicks on a label button
        this.selectedLabel = label;
        // clear canvas for redrawing
        this.points_available = [];
        clearInterval(this.canvasRefreshInterval);
        var canvas = document.getElementById('canvas');
        var ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = "red";
        ctx.font = "15px Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = "red";
        // initialize lists of points and markers to be drawn
        var pointsMap = new Map();
        var markers = [];
        var es_data = this.elasticsearch_data
        var instance = 0;
        es_data.forEach(function (record) {
          record.Name = "Pose"
          if (record.Name === label) {
            markers.push({'time': record.Timestamp/1000, 'text': record.Name, 'overlayText': record.Name})
            // Save points info if it exists
            if (record.points) {
              // Use time resolution of 0.1 second
              const timestamp = Math.round(record.Timestamp/100);
              if (pointsMap.has(timestamp)) {
                const pointsinfo = {'instance':instance++, 'timestamp':Math.ceil(record.Timestamp/100), 'name':record.Name, 'confidence':record.confidence, 'points':record.points};
                
                // 'x':record.points.Left*canvas.width, 'y':record.points.Top*canvas.height, 'width':record.points.Width*canvas.width, 'height':record.points.Height*canvas.height};
                pointsMap.get(timestamp).push(pointsinfo)
              } else {
                instance = 0;
                const pointsinfo = {'instance':instance++, 'timestamp':Math.ceil(record.Timestamp/100), 'name':record.Name, 'confidence':record.confidence, 'points':record.points};
                //'x':record.points.Left*canvas.width, 'y':record.points.Top*canvas.height, 'width':record.points.Width*canvas.width, 'height':record.points.Height*canvas.height};
                pointsMap.set(timestamp, [pointsinfo])
              }
            }
          }
        }.bind(this));
        if (pointsMap.size > 0) {
          this.drawPoints(pointsMap);
        }
        // redraw markers on video timeline
        this.player.markers.removeAll();
        this.player.markers.add(markers);
      },
      async fetchAssetData () {
          let query = 'AssetId:'+this.$route.params.asset_id+' Operator:'+this.operator;//+' Workflow: 52803f91-8790-4a1f-b911-1b0a49af76b9';
          //table tennis ' Workflow: 52803f91-8790-4a1f-b911-1b0a49af76b9';
          //2 speakers ' Workflow: c8af43e1-1173-42ab-8015-49148c71611c';
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
            let es_data = []
            let result = await response
            let data = result.hits.hits
            if (data.length === 0 && this.Confidence > 55) {
                this.lowerConfidence = true
                this.lowerConfidenceMessage = 'Try lowering confidence threshold'
            }
            else {
              this.lowerConfidence = false
              for (var i = 0, len = data.length; i < len; i++) {
                es_data.push(data[i]._source)
              }
            }
            this.elasticsearch_data = JSON.parse(JSON.stringify(es_data))
            this.isBusy = false
        }
      },
      drawPoints: function(pointsMap) {
        var canvas = document.getElementById('canvas');
        var ctx = canvas.getContext('2d');
        // If user just clicked a new label...
        if (this.canvasRefreshInterval != undefined) {
          // ...then reset the old canvas refresh interval.
          clearInterval(this.canvasRefreshInterval)
        }
        // Look for and draw bounding points every 100ms
        //const interval_ms = 100;
        //changed from 100 to 1000
        const interval_ms = 100;
        const erase_on_iteration = 2;
        var i = 0;
        //if both points have confidence greater than keypoint threshold
        //AND
        //both points are in the list of joint pairs as defined by https://github.com/dmlc/gluon-cv/blob/master/gluoncv/utils/viz/keypoints.py
        //joint_visible = confidence[:, :, 0] > keypoint_thresh
        var joint_pairs = [[0, 1], [1, 3], [0, 2], [2, 4],
                   [5, 6], [5, 7], [7, 9], [6, 8], [8, 10],
                   [5, 11], [6, 12], [11, 12],
                   [11, 13], [12, 14], [13, 15], [14, 16]];

        var model_width = 740; //alpha pose model is using this size in its transformations
        var model_height = 416; //alpha pose model is using this size in its transformations

        this.canvasRefreshInterval = setInterval(function () {
          i++;
          // erase old bounding points
          if (!this.player.paused() && i % erase_on_iteration === 0) {
            i=0;
            console.log("erasing *************************")
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.beginPath();
            ctx.strokeStyle = "red";
            ctx.font = "15px Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "red";
          }
          // Get current player timestamp to the nearest 1/10th second
          var player_timestamp = Math.round(this.player.currentTime()*10.0);

          var x_scale = canvas.width /model_width;
          var y_scale = canvas.height/model_height;
          //console.log("x_scale is " + x_scale);
          //console.log("y_scale is " + y_scale);

          // If we have a pose for the player's timestamp...
          if (pointsMap.has(player_timestamp)) {
            var joints = (pointsMap.get(player_timestamp))[0];
            //for each joint pair instance 
            for (var j=0; j < joint_pairs.length; j++) {
                var joint1 = joint_pairs[j][0];
                var joint2 = joint_pairs[j][1];
                //console.log("joint1 is" + joint1)
                //console.log("joint2 is " + joint2)
                if(joints.confidence[joint1][0] > 0.2 && joints.confidence[joint2][0] > 0.2) {

                    ctx.moveTo(joints.points[joint1][0] * x_scale,joints.points[joint1][1] * y_scale);
                    ctx.lineTo(joints.points[joint2][0]* x_scale,joints.points[joint2][1] * y_scale);
                    ctx.fillRect(joints.points[joint1][0]* x_scale,joints.points[joint1][1] * y_scale,5,5);
                    ctx.fillRect(joints.points[joint2][0]* x_scale,joints.points[joint2][1] * y_scale,5,5);

                    //console.log("drawing segment from " + joint1 + " to " + joint2)
                }
            }
          }
          //ctx.closePath();
          ctx.stroke();
        }.bind(this), interval_ms);
      },
      chartData() {
        var timeseries = new Map();
        function saveTimestamp (millisecond) {
          if (timeseries.has(millisecond)) {
            timeseries.set(millisecond, {"x": millisecond, "y": timeseries.get(millisecond).y + 1})
          } else {
            timeseries.set(millisecond, {"x": millisecond, "y":1})
          }
        }
        var es_data = this.elasticsearch_data;
        es_data.forEach( function(record) {
          // Define timestamp with millisecond resolution
          record.Name = "Pose"
          const millisecond = Math.round(record.Timestamp);
          if (this.selectedLabel) {
            // No label has been selected, so enumerate timestamps for all label names.
            if (record.Name === this.selectedLabel) {
              saveTimestamp(millisecond);
            }
          } else {
            // Label is undefined. Enumerate timestamps for all label names.
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