<template>
  <div id="videoplayer" class="videoplayer">
    <video ref="videoPlayer" width=600 height=300 data-setup='{ "inactivityTimeout": 0 }' class="video-js vjs-fluid vjs-default-skin" controls>
       <source v-bind:src="video_url" type="video/mp4">
       <canvas class="canvas" id="canvas" width="600" height="300"></canvas> 
    </video>  
  </div>
</template>

<script>
import videojs from 'video.js'
import '@/../node_modules/video.js/dist/video-js.css'
import '@/../node_modules/videojs-markers/dist/videojs.markers.css'
import '@/../node_modules/videojs-markers/dist/videojs-markers.js'

export default {
  data: function () {
    return {
      video_url: '',
      player: null
    }
  },
  name: 'VideoPlayer',
  props: {
        options: {
            type: Object,
            default() {
                return {};
            }
        }
  },
  beforeDestroy() {
        if (this.player) {
            this.player.dispose()
            this.$store.commit('updatePlayer', null)
        }
  },
  created() {
    const video_url = this.options.sources[0].src
    this.video_url = video_url
  },
  mounted: function () {
    console.log('mount')
    // Fill canvas overlay red and draw a rectangle
    var canvas = document.getElementById('canvas');
    var ctx = canvas.getContext('2d');
    ctx.rect(20, 20, 150, 100);
    // Uncomment to draw rectangle:
    // ctx.stroke();
    this.player = videojs(this.$refs.videoPlayer)
      this.player.ready( () => {
      console.log('player', this.player)
      this.player.loop(true)
      this.player.markers({
        breakOverlay: {
          display: true,
          displayTime: 1,
          text: function (marker) {
            return marker.overlayText;
          }
        },
        markers: []
        });
      this.player.autoplay('muted')
      this.player.currentTime(0)
      this.$store.commit('updatePlayer', this.player)
    })
  },
  beforeUpdate: function () {
    this.$store.commit('updatePlayer', this.player)
  } 
}
</script>

<style scoped>
  .canvas {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 10;
    pointer-events: none;
  }
</style>