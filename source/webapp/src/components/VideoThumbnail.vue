<template>
  <div style="position: relative;">
    <b-container>
      <b-img
        :id="thumbnailID"
        rounded
        fluid
        :src="signedUrl"
        alt="Thumbnail image is not available."
      />
    </b-container>
  </div>
</template>

<script>
import '@/../node_modules/video.js/dist/video-js.css'

export default {
  name: 'VideoThumbnail',
  props: ['thumbnailID', 'signedUrl'],
}
</script>

<style scoped>
</style>
