<template>
  <div>
    <Header />
    <b-container fluid>
      <b-alert
        v-model="showElasticSearchAlert"
        variant="danger"
        dismissible
      >
        Elasticsearch server denied access. Please check its access policy.
      </b-alert>
      <b-row class="dataColumns">
        <b-col>
          <div>
            <b-row align-h="center">
              <b-tabs
                content-class="mt-3"
                fill
              >
                <b-tab
                  title="ML Vision"
                  active
                  @click="currentView = 'LabelObjects'; mlTabs = 0"
                >
                  <b-container fluid>
                    <b-row>
                      <div>
                        <b-tabs
                          v-model="mlTabs"
                          content-class="mt-3"
                          fill
                        >
                          <b-tab
                            title="Objects"
                            @click="currentView = 'LabelObjects'"
                          />
                          <b-tab
                            title="Celebrities"
                            @click="currentView = 'Celebrities'"
                          />
                          <b-tab
                            title="Moderation"
                            @click="currentView = 'ContentModeration'"
                          />
                          <b-tab
                            title="Faces"
                            @click="currentView = 'FaceDetection'"
                          />
                        </b-tabs>
                      </div>
                    </b-row>
                  </b-container>
                </b-tab>
                <b-tab
                  v-if="mediaType !== 'image/jpg'"
                  title="Speech Recognition"
                  @click="currentView = 'Transcript'; speechTabs = 0"
                >
                  <b-tabs
                    v-model="speechTabs"
                    content-class="mt-3"
                    fill
                  >
                    <b-tab
                      title="Transcript"
                      @click="currentView = 'Transcript'"
                    />
                    <b-tab
                      title="Translation"
                      @click="currentView = 'Translation'"
                    />
                    <b-tab
                      title="KeyPhrases"
                      @click="currentView = 'KeyPhrases'"
                    />
                    <b-tab
                      title="Entities"
                      @click="currentView = 'Entities'"
                    />
                  </b-tabs>
                </b-tab>
              </b-tabs>
            </b-row>
          </div>
          <div>
            <keep-alive>
              <component :is="currentView" :mediaType="mediaType">
                <!-- inactive components will be cached! -->
              </component>
            </keep-alive>
          </div>
        </b-col>
        <b-col>
          <div v-if="mediaType === 'image/jpg'">
            <!-- TODO: rename videoOptions since its not always a video -->
            <div v-if="videoOptions.sources[0].src === ''">
              <Loading />
            </div>
            <div v-else>
              <ImageFeature :options="videoOptions" />
            </div>
          </div>
          <div v-else>
            <div v-if="videoOptions.sources[0].src === ''">
              <Loading />
            </div>
            <div v-else>
              <VideoPlayer :options="videoOptions" />
              <LineChart />
            </div>
          </div>
          <div>
            <b-row class="mediaSummary">
              <MediaSummaryBox
                :s3Uri="s3_uri"
                :filename="filename"
                :videoUrl="videoOptions.sources[0].src"
              />
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
  import ImageFeature from '@/components/ImageFeature.vue'
  import Loading from '@/components/Loading.vue'
  import ComponentLoadingError from '@/components/ComponentLoadingError.vue'
  import MediaSummaryBox from '@/components/MediaSummaryBox.vue'
  import LineChart from '@/components/LineChart.vue'
  import { mapState } from 'vuex'

  export default {
    name: 'Home',
    components: {
      Header,
      ComponentLoadingError,
      MediaSummaryBox,
      Loading,
      VideoPlayer,
      ImageFeature,
      LineChart,
      LabelObjects: () => ({
        component: new Promise(function(resolve) {
          setTimeout(function() {
            resolve(import('@/components/LabelObjects.vue'));
        }, 1000);
        }),
        loading: Loading
      }),

      Celebrities: () => ({
        component: new Promise(function(resolve) {
          setTimeout(function() {
            resolve(import('@/components/Celebrities.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),

      ContentModeration: () => ({
        component: new Promise(function(resolve) {
          setTimeout(function() {
            resolve(import('@/components/ContentModeration.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),
      Transcript: () => ({
        component: new Promise(function(resolve) {
          setTimeout(function() {
            resolve(import('@/components/Transcript.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),
      Translation: () => ({
        component: new Promise(function(resolve) {
          setTimeout(function() {
            resolve(import('@/components/Translation.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),
      FaceDetection: () => ({
        component: new Promise(function(resolve) {
          setTimeout(function() {
            resolve(import('@/components/FaceDetection.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),
      Entities: () => ({
        component: new Promise(function(resolve) {
          setTimeout(function() {
            resolve(import('@/components/ComprehendEntities.vue'));
        }, 1000);
        }),
        loading: Loading,
      }),
      KeyPhrases: () => ({
        component: new Promise(function(resolve) {
          setTimeout(function() {
            resolve(import('@/components/ComprehendKeyPhrases.vue'));
        }, 1000);
        }),
        loading: Loading,
        error: ComponentLoadingError
      })
    },
    data: function () {
      return {
        s3_uri: '',
        filename: '',
        currentView: 'LabelObjects',
        showElasticSearchAlert: false,
        mlTabs: 0,
        speechTabs: 0,
        mediaType: "",
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
    computed: {
      ...mapState(['Confidence'])
    },
    created() {
          this.getAssetMetadata();
      },
    methods: {
      async getAssetMetadata () {
          const token = await this.$Amplify.Auth.currentSession().then(data =>{
            var accessToken = data.getIdToken().getJwtToken()
            return accessToken
          })
          var asset_id = this.$route.params.asset_id;
          fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT+'/metadata/'+asset_id, {
            method: 'get',
            headers: {
              'Authorization': token
            }
          }).then(response => {
            response.json().then(data => ({
                data: data,
              })
            ).then(res => {
              this.s3_uri = 's3://'+res.data.results.S3Bucket+'/'+res.data.results.S3Key
              this.filename = this.s3_uri.split("/").pop();
              if (this.filename.substring(this.filename.lastIndexOf(".")) === ".jpg") {
                this.mediaType = "image/jpg"
              }
              if (this.filename.substring(this.filename.lastIndexOf(".")) === ".mp4") {
                this.mediaType = "video/mp4"
              }
              this.getVideoUrl()
            })
          });
          this.updateAssetId();
      },
      async getVideoUrl() {
        // This function gets the video URL then initializes the video player
        const token = await this.$Amplify.Auth.currentSession().then(data =>{
          var accessToken = data.getIdToken().getJwtToken()
          return accessToken
        })
        var bucket = this.s3_uri.split("/")[2];
        var key = this.s3_uri.split(this.s3_uri.split("/")[2] + '/')[1];
        // get URL to video file in S3
        fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT + '/download', {
          method: 'POST',
          mode: 'cors',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token
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
      }
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
