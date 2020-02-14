<template>
  <b-container fluid>
    <b-img id="imageFeature" fluid :src="image_url" @load="onImageLoad"></b-img>
    <canvas
      id="canvas"
      class="canvas"
    />
  </b-container>
</template>

<script>
export default {
  name: 'ImageFeature',
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
      image_url: '',
    }
  },
  beforeDestroy() {
  },
  created() {
    const _image_url = this.options.sources[0].src;
    this.image_url = _image_url
  },
  mounted: function () {
    window.addEventListener('resize', function () {
      // Update canvas size when window is resized
      var canvas = document.getElementById('canvas');
      var image_feature = document.getElementById('imageFeature');
      canvas.width = image_feature.clientWidth;
      canvas.height = image_feature.clientHeight;
    });
  },
  methods: {
    onImageLoad() {
      // Set canvas size to videoPlayer size
      var canvas = document.getElementById('canvas');
      var image_feature = document.getElementById('imageFeature');
      canvas.width = image_feature.clientWidth;
      canvas.height = image_feature.clientHeight;
    },
  },
}
</script>

<style scoped>
  .canvas {
    position: absolute;
    top: 0;
    left: 30px;
    /*background-color:rgba(255,0,0,0.5);*/
    pointer-events: none;
  }
</style>
