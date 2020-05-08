<template>
  <b-container>
    <div id="waveform">
      <!-- Here be waveform -->
    </div>
    <div id="wave-timeline"></div>
  </b-container>
</template>

<script>
  import { mapState } from 'vuex'
  import WaveSurfer from 'wavesurfer.js';
  import Timeline from 'wavesurfer.js/dist/plugin/wavesurfer.timeline.js';

  export default {
    name: "Waveform",
    data() {
      return {
        wavesurfer: Object,
        wavesurfer_ready: false,
        old_position: 0
      }
    },
    computed: {
      ...mapState(['player']),
    },
    mounted() {
      this.getWorkflowId();
      this.getTimeUpdate()
    },
    beforeDestroy: function () {
    },
    methods: {
      async getAssetAudio(bucket, s3Key) {
        const token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
        const data = { "S3Bucket": bucket, "S3Key": s3Key };
        let response = await fetch(this.DATAPLANE_API_ENDPOINT + '/download',   {
          method: 'POST',
          mode: 'cors',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token
          },
          body: JSON.stringify(data)
        });
        if (response.status === 200) {
          await response.text().then(url => {
            this.renderWaveform(url)
          });
        }
      },
      async getWorkflowId() {
        const token = await this.$Amplify.Auth.currentSession().then(data =>{
          return data.getIdToken().getJwtToken();
        });
        const asset_id = this.$route.params.asset_id
        fetch(this.WORKFLOW_API_ENDPOINT + '/workflow/execution/asset/' + asset_id, {
          method: 'get',
          headers: {
            'Authorization': token
          }
        }).then(response => {
          response.json().then(data => ({
              data: data,
            })
          ).then(res => {
            const workflow_id = res.data[0].Id
            fetch(this.WORKFLOW_API_ENDPOINT + '/workflow/execution/' + workflow_id, {
              method: 'get',
              headers: {
                'Authorization': token
              }
            }).then(response => {
                response.json().then(data => ({
                    data: data,
                  })
                ).then(res => {
                  const bucket = res.data.Globals.Media.Audio.S3Bucket;
                  const s3Key = res.data.Globals.Media.Audio.S3Key;
                  this.getAssetAudio(bucket, s3Key);
                  }
                )
              }
            )
            }
            )
          }
        )
      },
      renderWaveform(url) {
        const vm = this;
        let wavesurfer = WaveSurfer.create({
          container: '#waveform',
          removeMediaElementOnDestroy: true,
          closeAudioContext: true,
          cursorColor: "red",
          progressColor: "#999",
          responsive: true,
          height: 64,
          barHeight: 2,
          plugins: [
            Timeline.create({
              container: '#wave-timeline'
            }),
          ]
        });
        wavesurfer.cancelAjax()
        wavesurfer.load(url);
        vm.wavesurfer = wavesurfer
        wavesurfer.on('ready', function () {
          vm.wavesurfer_ready = true;
        });
        wavesurfer.on('seek', function (new_position) {
          // In order to distinguish between interactive user clicks and
          // seeks from the getTimeUpdate() function, we need to do this:
          // Don't seek if new position within 3 seconds from the old position.
          // Hopefully all user clicks will be 3 seconds away from the old position.
          if (Math.abs(new_position*wavesurfer.getDuration() - vm.old_position*wavesurfer.getDuration()) < 3) {
            vm.old_position = new_position;
            return;
          }
          // Seek the video player to the new position
          vm.player.currentTime(new_position*wavesurfer.getDuration())
          vm.old_position = new_position
          // Send a signal to the Transcript component so it can
          // seek the caption table to the new position.
          vm.$store.commit('updateWaveformSeekPosition', new_position*wavesurfer.getDuration());
        });
      },
      getTimeUpdate() {
        const vm = this;
        // Send current time position for the video player to verticalLineCanvas
        var last_position = 0;
        if (this.player) {
          this.player.on('timeupdate', function () {
            const current_position = Math.round(this.player.currentTime() / this.player.duration() * 1000);
            if (current_position !== last_position) {
              if (vm.wavesurfer_ready) {
                vm.wavesurfer.seekTo(current_position/1000);
              }
              last_position = current_position;
            }
          }.bind(this));
        }
      },
    }
  }
</script>

<style scoped>
</style>
