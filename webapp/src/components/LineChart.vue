<template>
  <b-container>
    <div v-if="isBusy">
      <Loading />
    </div>
    <div v-else>
      <div id="container">
        <canvas id="lineChart" @click="handleClick"></canvas>
        <canvas id="verticalLineCanvas" class="canvas"></canvas>
      </div>
    </div>
  </b-container>
</template>

<script>
  import { mapState } from 'vuex'
  import Chart from 'chart.js';
  import Loading from '@/components/Loading.vue'

  export default {
    name: "LineChart",
    components: {
      Loading
    },
    data() {
      return {
        duration: undefined,
        chartConfig: {},
        chart: undefined,
        isBusy: false
      }
    },
    computed: {
      ...mapState(['chart_tuples', 'selected_label', 'player']),
    },
    watch: {
      chart_tuples: function() {
        this.renderLineChart();
      },
      player: function() {
        this.getDuration();
        this.getTimeUpdate();
        this.renderLineChart();
      },
    },
    deactivated: function () {
      console.log('deactivated component:', this.operator);
      this.chart = Object
    },
    activated: function () {
      console.log('activated component:', this.operator)
    },
    beforeDestroy: function () {
      this.chart = Object
    },
    mounted: function () {
      this.chartConfig = {
        type: 'scatter',
        data: {
          labels: [0],
          datasets: [{
            data: [0],
            borderColor: "#3e95cd",
            borderWidth: 3,
            fill: false,
            showLine: false
          }]
        },
        options: {
          legend: {
            display: false
          },
          title: {
            display: true,
            text: ''
          },
          tooltips: {
            enabled: false
          },
          responsive: true,
          maintainAspectRatio: false,
          aspectRatio: 1.5,
          scales: {
            yAxes: [{
              display: true,
              fixedStepSize: 1,
              scaleLabel: {
                display: true,
                labelString: 'Label Quantity'
              },
              ticks: {
                beginAtZero: true,
                min: 0,
                padding: 25,
                callback: function(value) {
                  if (Math.floor(value) === value) {
                    return value;
                  }
                }
              }
            }],
            xAxes: [{
              display: true,
              scaleLabel: {
                display: true,
                labelString: 'Time (mm:ss)'
              },
              ticks: {
                beginAtZero: true,
                minRotation: 30,
                min: 0,
                callback: function(milliseconds) {
                  if (milliseconds >= 3600000) {
                    return new Date(milliseconds).toISOString().substr(11, 12);
                  } else {
                    // drop hours portion if time is less than 1 hour
                    return new Date(milliseconds).toISOString().substr(14, 9);
                  }
                }
              }
            }]
          },
        }
      };
      window.addEventListener('resize', function () {
        // TODO: set chart and canvas width equal to video player width
        // TODO: make columns resize equally when resizing window
        // Update canvas size when window is resized
        var chart = document.getElementById('lineChart');
        var canvas_overlay = document.getElementById('verticalLineCanvas');
        canvas_overlay.width=chart.width;
        canvas_overlay.height=chart.height;

      });
    },
    methods: {
      handleClick(event) {
        var canvas_overlay = document.getElementById('verticalLineCanvas');
        if (canvas_overlay){
          const chart_width = this.chart.chart.chartArea.right - this.chart.chart.chartArea.left;
          const chart_left = this.chart.chart.chartArea.left;
          // Ignore clicks that are on the chart but to the left of the y-axis
          if (event.offsetX < chart_left) {
            return
          }
          if (this.duration > 0) {
            // Calculate click position as a percentage of chart width, to 1/10th precision.
            const percentage = Math.round((event.offsetX - chart_left) / chart_width * 1000) / 10;
            this.player.currentTime(this.duration * percentage / 100)
          }
        }
      },
      getDuration() {
        // Get the duration for the video player source
        if (this.player) {
          this.player.on('loadedmetadata', function () {
            this.duration = this.player.duration();
          }.bind(this));
        }
      },
      getTimeUpdate() {
        // Send current time position for the video player to verticalLineCanvas
        var last_position = 0;
        if (this.player) {
          this.player.on('timeupdate', function () {
            const current_position = Math.round(this.player.currentTime() / this.player.duration() * 1000);
            if (current_position !== last_position) {
              this.drawVerticleLine(current_position/1000);
              last_position = current_position;
            }
          }.bind(this));
        }
      },
      renderLineChart() {
        const lengthOfVideo = this.duration;
        const data = this.chart_tuples;
        const ctx = document.getElementById('lineChart');
        this.chartConfig.options.title.text = this.selected_label ? this.selected_label + " (instances / sec)" : "Total Labels (instances / sec)";
        if (this.chart === undefined) {
          this.chart = new Chart(ctx, {
            type: this.chartConfig.type,
            data: {
              datasets: [{
                data: data
              }]
            },
            options: this.chartConfig.options,
          });
        } else {
          this.chart.options.title.text = this.selected_label ? this.selected_label + " (instances / sec)" : "Total Labels (instances / sec)";
          if (lengthOfVideo) {
            this.chart.options.scales.xAxes[0].ticks.max = lengthOfVideo*1000;
          }
          if (lengthOfVideo > 3600) {
            this.chart.options.scales.xAxes[0].scaleLabel.labelString = "Time (hh:mm:ss)";
          }

          this.chart.data.datasets[0].data = null;
          this.chart.data.datasets[0].data = data;
          this.chart.lineAtIndex = .25;
          this.chart.update();
        }
        // Place canvas over line chart
        var canvas_overlay = document.getElementById('verticalLineCanvas');
        canvas_overlay.width=this.chart.width;
        canvas_overlay.height=this.chart.height;
      },
      drawVerticleLine(position) {
        var canvas_overlay = document.getElementById('verticalLineCanvas');
        if (!canvas_overlay) return;
        var ctx = canvas_overlay.getContext('2d');
        if (!ctx || !this.chart) return;
        var scale = this.chart.scales['y-axis-1'];
        var lineLeftOffset = (this.chart.chart.chartArea.right - this.chart.chart.chartArea.left) * position + this.chart.chart.chartArea.left;
        ctx.clearRect(0, 0, canvas_overlay.width, canvas_overlay.height);
        ctx.beginPath();
        ctx.strokeStyle = '#ff0000';
        ctx.moveTo(lineLeftOffset, scale.top);
        ctx.lineTo(lineLeftOffset, scale.bottom+10);
        ctx.stroke();
      }
    }
  }
</script>

<style scoped>
  #container { position: relative; }
  .canvas {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
  }
</style>
