<template>
  <div style="position: relative;">
    <b-container>
      <b-img :id="ThumbnailID" rounded fluid :src="signed_url" alt="thumbnail image"></b-img>
    </b-container>
  </div>
</template>

<script>
import videojs from 'video.js'
import '@/../node_modules/video.js/dist/video-js.css'

export default {
  name: 'VideoThumbnail',
  props: ['ThumbnailID', 'signed_url'],
}
</script>

<style scoped>
</style>
