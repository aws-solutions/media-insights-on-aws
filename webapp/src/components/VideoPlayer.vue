<template>
  <b-container fluid>
    <video
      id="videoPlayer"
      ref="videoPlayer"
      width="600"
      height="300"
      data-setup="{ &quot;inactivityTimeout&quot;: 0 }"
      class="video-js vjs-fluid vjs-default-skin"
      controls
      playsinline
    >
      <source
        :src="video_url"
        type="video/mp4"
      >
    </video>
    <canvas
      id="canvas"
      class="canvas"
    />
  </b-container>
</template>

<script>
import videojs from 'video.js'
import '@/../node_modules/video.js/dist/video-js.css'
import '@/../node_modules/videojs-markers/dist/videojs.markers.css'
import '@/../node_modules/videojs-markers/dist/videojs-markers.js'
import '@/../node_modules/videojs-hotkeys/build/videojs.hotkeys.min.js'

export default {
  name: 'VideoPlayer',
  props: {
    options: {
      type: Object,
      default() {
        return {};
      }
    }
  },
  data: function () {
    return {
      video_url: '',
      player: null
    }
  },
  beforeDestroy() {
    if (this.player) {
      this.player.dispose();
      this.$store.commit('updatePlayer', null)
    }
  },
  created() {
    const video_url = this.options.sources[0].src;
    this.video_url = video_url
  },
  mounted: function () {
    this.player = videojs(this.$refs.videoPlayer);
    this.player.ready(() => {
      this.player.hotkeys({
        volumeStep: 0.1,
        seekStep: 1,
        enableVolumeScroll: false,
        enableNumbers: false,
        enableModifiersForNumbers: false
      });
      this.player.loop(true);
      this.player.markers({
        breakOverlay: {
          display: false,
        },
        markerTip: {
          display: true,
          text: function (marker) {
            return marker.text;
          }
        },
        markers: []
      });
      this.player.autoplay('muted');
      this.player.currentTime(0);
      this.$store.commit('updatePlayer', this.player);

      // Set canvas size to videoPlayer size
      var canvas = document.getElementById('canvas');
      var video = document.getElementById('videoPlayer');
      canvas.width = video.clientWidth;
      canvas.height = video.clientHeight;
    });
    window.addEventListener('resize', function () {
      // Update canvas size when window is resized
      var canvas = document.getElementById('canvas');
      var video = document.getElementById('videoPlayer');
      canvas.width = video.clientWidth;
      canvas.height = video.clientHeight;
    });
  },
  beforeUpdate: function () {
    this.$store.commit('updatePlayer', this.player)
  }
}
</script>

<style>
  .video-js .vjs-current-time, .vjs-no-flex .vjs-current-time {
    display: block; }
</style>
<style scoped>
  .canvas {
    position: absolute;
    top: 0;
    left: 30px;
    /*background-color:rgba(255,0,0,0.5);*/
    pointer-events: none;
  }
</style>
