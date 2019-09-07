<template>
  <div>
    <Header />
    <b-container fluid>
      <b-alert v-model="showElasticSearchAlert" variant="danger" dismissible>
        Elasticsearch server denied access. Please check its access policy.
      </b-alert>
      <b-row class="dataColumns">
        <b-col>
          <div>
            <b-row  align-h="center">
            <b-tabs content-class="mt-3" fill>
              <b-tab @click="currentView = 'LabelObjects'; mlTabs = 0" title="ML Vision" active>
              <b-container fluid>
                <b-row>
                  <div>
                    <b-tabs v-model="mlTabs" content-class="mt-3" fill>
                      <b-tab @click="currentView = 'LabelObjects'" title="Objects"></b-tab>
                      <b-tab @click="currentView = 'Celebrities'" title="Celebrities"></b-tab>
                      <b-tab @click="currentView = 'ContentModeration'" title="Moderation"></b-tab>
                      <b-tab @click="currentView = 'FaceDetection'" title="Faces"></b-tab>
                    </b-tabs>
                  </div>
                </b-row>
              </b-container>
              </b-tab>
              <b-tab @click="currentView = 'Transcript'; speechTabs = 0" title="Speech Recognition">
                <b-tabs v-model="speechTabs" content-class="mt-3" fill>
                  <b-tab @click="currentView = 'Transcript'" title="Transcript"></b-tab>
                  <b-tab @click="currentView = 'Translation'" title="Translation"></b-tab>
                  <b-tab @click="currentView = 'KeyPhrases'" title="KeyPhrases"></b-tab>
                  <b-tab @click="currentView = 'Entities'" title="Entities"></b-tab>
                </b-tabs>
              </b-tab>
            </b-tabs>
            </b-row>
          </div>
          <div>
            <keep-alive>
              <component v-bind:is="currentView">
                <!-- inactive components will be cached! -->
              </component>
            </keep-alive>
        </div>
        </b-col>
        <b-col>
          <div v-if="this.videoOptions.sources[0].src === ''">
            <Loading />
          </div>
          <div v-else>
            <VideoPlayer :options="videoOptions"></VideoPlayer>
          </div>
          <div>
            <b-row class='mediaSummary'>
            <MediaSummaryBox :s3_uri=s3_uri :filename=filename />
            </b-row>
          </div>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
  import Header from '@/components/Header.vue'
  import VideoPlayer from '@/components/VideoPlayer.vue'
  import Loading from '@/components/Loading.vue'
  import ComponentLoadingError from '@/components/ComponentLoadingError.vue'
  import MediaSummaryBox from '@/components/MediaSummaryBox.vue'
  import { mapState } from 'vuex'

  export default {
    name: 'Home',
    data: function () {
      return {
        s3_uri: '',
        filename: '',
        currentView: 'LabelObjects',
        showElasticSearchAlert: false,
        mlTabs: 0,
        speechTabs: 0,
        signed_url: '',
        videoOptions: {
          preload: 'auto',
          loop: true,
				  controls: true,
				  sources: [
					    {
						    src: "",
						    type: "video/mp4"
					    }
				  ]
			  }
      }
    },
    components: {
      Header,
      ComponentLoadingError,
      MediaSummaryBox,
      Loading,
      VideoPlayer,
      LabelObjects: () => ({
        component: new Promise(function(resolve, reject) {
          setTimeout(function() {
            resolve(import('@/components/LabelObjects.vue'));
        }, 1000);
        }),
        loading: Loading
      }),

      Celebrities: () => ({
        component: new Promise(function(resolve, reject) {
          setTimeout(function() {
            resolve(import('@/components/Celebrities.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),

      ContentModeration: () => ({
        component: new Promise(function(resolve, reject) {
          setTimeout(function() {
            resolve(import('@/components/ContentModeration.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),
      Transcript: () => ({
        component: new Promise(function(resolve, reject) {
          setTimeout(function() {
            resolve(import('@/components/Transcript.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),
      Translation: () => ({
        component: new Promise(function(resolve, reject) {
          setTimeout(function() {
            resolve(import('@/components/Translation.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),
      FaceDetection: () => ({
        component: new Promise(function(resolve, reject) {
          setTimeout(function() {
            resolve(import('@/components/FaceDetection.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),
      Entities: () => ({
        component: new Promise(function(resolve, reject) {
          setTimeout(function() {
            resolve(import('@/components/ComprehendEntities.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),
      KeyPhrases: () => ({
        component: new Promise(function(resolve, reject) {
          setTimeout(function() {
            resolve(import('@/components/ComprehendKeyPhrases.vue'));
        }, 1000);
        }),
        loading: Loading,
        error: ComponentLoadingError
      })
    },
    methods: {
      getVideoUrl() {
        // This function gets the video URL then initializes the video player
        var bucket = this.s3_uri.split("/")[2];
        var key = this.s3_uri.split(this.s3_uri.split("/")[2] + '/')[1];
        // get URL to video file in S3
        fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT + '/download', {
          method: 'POST',
          mode: 'cors',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({"S3Bucket": bucket, "S3Key": key})
        }).then(data => {
            data.text().then((data) => {
            this.videoOptions.sources[0].src = data
        }).catch(err => console.error(err));
        })
      },
      updateAssetId () {
        this.$store.commit('updateAssetId', this.$route.params.asset_id);
      },
      checkServerAccess () {
        fetch(process.env.VUE_APP_ELASTICSEARCH_ENDPOINT, {
          method: 'get'
        }).then(response =>
          response.json().then(data => ({
              data: data,
              status: response.status
            })
          ).then(res => {
            if (res.status == 403) {
              this.showElasticSearchAlert = true
            }
          })
        );
      }
    },
    created() {
          this.checkServerAccess();
          var asset_id = this.$route.params.asset_id;
          fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT+'/metadata/'+asset_id, {
            method: 'get'
          }).then(response => {
            response.json().then(data => ({
                data: data,
              })
            ).then(res => {
              this.s3_uri = 's3://'+res.data.results.S3Bucket+'/'+res.data.results.S3Key
              this.filename = this.s3_uri.split("/").pop();
              this.getVideoUrl()
            })
          });
          this.updateAssetId();
      },
    computed: {
      ...mapState(['Confidence'])
    }
  }
</script>

<style>
  #app {
    font-family: 'Avenir', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }

  .mediaSummary {
    text-align: left;
  }

  @media screen and (max-width: 800px) {
  .dataColumns {
    flex-direction: column-reverse;
  }
}

</style>
