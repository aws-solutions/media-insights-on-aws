<template>
  <b-container fluid>
    <b-row
      align-v="center"
      class="my-1"
    >
      <b-col>
        <label>Asset ID:</label>
        {{ this.$route.params.asset_id }}
        <br>
        <label>Filename:&nbsp;</label>
        <a
          :href="videoUrl"
          download
        >
          {{ filename }}
        </a>
        <br>
        <label>Duration:</label>
        {{ duration }}
      </b-col>
    </b-row>
    <br>
  </b-container>
</template>

<script>
  import { mapState } from 'vuex'
  export default {
    name: 'MediaSummary',
    props: ['s3Uri','filename','videoUrl'],
    data () {
      return {
        duration: undefined
      }
    },
    computed: {
      ...mapState(['player']),
    },
    watch: {
      player: function() {
        this.getDuration();
      },
    },
    deactivated: function () {
      console.log('deactivated component:', this.operator)
      this.lineChart = Object
    },
    activated: function () {
      console.log('activated component:', this.operator)
    },
    beforeDestroy: function () {
    },
    methods: {
      getDuration() {
        if (this.player) {
          this.player.on('loadedmetadata', function () {
            var seconds = this.player.duration();
            if (seconds >= 3600) {
              this.duration = new Date(seconds*1000).toISOString().substr(11, 8);
            } else {
              // drop hours portion if time is less than 1 hour
              this.duration = new Date(seconds*1000).toISOString().substr(14, 5);
            }
          }.bind(this));
        }
      }
    }
  }
</script>

<style>

</style>
