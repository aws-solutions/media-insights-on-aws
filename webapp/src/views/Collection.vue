<template>
  <div>
    <div class="headerTextBackground">
      <Header :is-collection-active="true" />
      <b-container fluid>
        <b-alert
          v-model="showElasticSearchAlert"
          variant="danger"
          dismissible
        >
          Elasticsearch error. Please check browser and elasticsearch access logs.
        </b-alert>
        <b-alert
          v-model="showDataplaneAlert"
          variant="danger"
          dismissible
        >
          Dataplane Error. Please check browser and dataplane logs.
        </b-alert>
        <b-alert
          v-model="showDeletedAlert"
          variant="success"
          dismissible
        >
          Successfully Deleted Asset
        </b-alert>
        <b-row align-h="center">
          <h1>Media Collection</h1>
        </b-row>
        <b-row
          align-h="center"
          class="tagline"
        >
          <b>Discover insights in your media by searching for keywords, objects, or even people.</b>
        </b-row>
        <b-row
          class="my-1"
          align-v="center"
          align-h="center"
        >
          <b-col sm="5">
            <input
              v-model="user_defined_query"
              type="text"
              placeholder="Search Collection..."
              @keyup.enter="searchCollection"
            >
          </b-col>
          <b-col sm="1">
            <b-button
              size="lg"
              @click="searchCollection"
            >
              Search
            </b-button>
          </b-col>
        </b-row>
      </b-container>
    </div>
    <b-container
      fluid
      class="resultsTable"
    >
      <b-row>
        <b-col>
          <div>
            <div class="column">
              <b-row class="my-1">
                <b-col>
                  <b-table
                    striped
                    hover
                    fixed
                    responsive
                    show-empty
                    :fields="fields"
                    :items="asset_list"
                    :sort-by.sync="sortBy"
                    :sort-desc.sync="sortDesc"
                    :current-page="currentPage"
                    :per-page="perPage"
                  >
                    <template v-slot:cell(Thumbnail)="data">
                      <VideoThumbnail
                        :thumbnail-i-d="data.item.thumbnailID"
                        :signed-url="data.item.signedUrl"
                      />
                    </template>
                    <template v-slot:cell(Actions)="data">
                      <b-button
                        variant="orange"
                        @click="$router.push(`/analysis/${data.item.asset_id}`)"
                      >
                        Analyze
                      </b-button>
                      &nbsp;
                      <b-button
                        :pressed="false"
                        variant="red"
                        @click="deleteAsset(`${data.item.asset_id}`)"
                      >
                        Delete
                      </b-button>
                    </template>
                  </b-table>
                  <div
                    v-if="noAssets"
                  >
                    <p> 
                      Looks like no assets have been uploaded! Try uploading <a href="upload">here</a>
                    </p>
                  </div>
                  <div
                    v-if="isBusy"
                    class="wrapper"
                  >
                    <Loading v-if="isBusy" />
                    <p class="text-muted">
                      (Loading...)
                    </p>
                  </div>
                </b-col>
              </b-row>
              <b-row align-h="center">
                <b-pagination
                  v-model="currentPage"
                  :total-rows="totalRows"
                  :per-page="perPage"
                  class="my-0"
                />
              </b-row>
            </div>
          </div>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
  import Header from '@/components/Header.vue'
  import VideoThumbnail from '@/components/VideoThumbnail.vue'
  import Loading from '@/components/Loading.vue'

  export default {
    name: "Run",
    components: {
      Header,
      Loading,
      VideoThumbnail
    },
    data() {
      return {
        showElasticSearchAlert: false,
        showDataplaneAlert: false,
        showDeletedAlert: false,
        totalRows: 1,
        noAssets: null,
        currentPage: 1,
        perPage: 10,
        isBusy: false,
        user_defined_query: "",
        asset_list: [],
        sortBy: 'Created',
        sortDesc: true,
        fields: [
            {
              'Thumbnail': {
              label: "Thumbnail",
              sortable: false
              }
            },
            {
              'Filename': {
              label: "File Name",
              sortable: true,
              tdClass: ["tableWordWrap"]
              }
            },
            {
              'status': {
              label: "Status",
              sortable: true,
              tdClass: ["tableWordWrap"]
              }
            },
            {
            'asset_id': {
              label: 'Asset ID',
              sortable: false,
              tdClass: ["tableWordWrap"]
              }
            },
            {
              'Created': {
              label: "Created",
              sortable: true,
              tdClass: ["tableWordWrap"]
              }
            },
            {
              'Actions': {
              label: 'Actions',
              sortable: false
              }
            }
        ]
      }
    },
    created: function () {
      this.isBusy = true
      this.retrieveAndFormatAsssets()
    },
    methods: {
      async deleteAsset(asset_id) {
        let token = await this.getAccessToken()
        let response = await fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT+'/metadata/'+asset_id, {
          method: 'delete',
          headers: {
            'Authorization': token
          }
        })
        if (response.status === 200) {
            this.showDeletedAlert = true
            this.asset_list = []
            this.retrieveAndFormatAsssets()
        }
        else {
            this.showDataplaneAlert = true
        }
      },
      async elasticsearchQuery (query) {
            let apiName = 'mieElasticsearch';
            let path = '/_search';
            let apiParams = {
              headers: {'Content-Type': 'application/json'},
              body: {
              "aggs" : {
                "distinct_assets" : {
                  "terms" : { "field" : "AssetId.keyword", "size" : 10000 }
                }
                }
              },
              queryStringParameters: {'q': query, '_source': 'AssetId'}
            }
            let response = await this.$Amplify.API.post(apiName, path, apiParams)
            if (!response) {
              this.showElasticSearchAlert = true
            }
            else {
              this.noAssets = false
              let result = await response
              return result
        }
      },
      async searchCollection () {
          this.noSearchResults = false
          this.isBusy = true
          let query = this.user_defined_query
          // if search is empty string then get asset list from dataplane instead of Elasticsearch.
          if (query === "") {
            this.showElasticSearchAlert = false;
            this.asset_list = [];
            this.retrieveAndFormatAsssets();
            this.isBusy = false
            return;
          }
          else {
            // Get the list of assets that contain metadata matching the user-specified search query.
            let elasticData = await this.elasticsearchQuery(query)
            if (elasticData.hits.total === 0) {
              // the search returned no data
              this.asset_list = []
              this.noSearchResults = true
              this.isBusy = false;
            }
            else {
              let assets = []
              this.asset_list = []
              this.noSearchResults = false
              let token = await this.getAccessToken()
              let buckets = elasticData.aggregations.distinct_assets.buckets
              for (var i = 0, len = buckets.length; i < len; i++) {
                let assetId = buckets[i].key
                let assetInfo = await this.getAssetInformation(token, assetId)
                if (assetInfo === null) {
                  continue
                }
                else {
                  assets.push(assetInfo)
                }
            }
            if (assets.length === 0) {
              this.noSearchResults = true
              this.isBusy = false
            }
            else {
              this.pushAssetsToTable(assets)
              this.totalRows = this.asset_list.length
              this.isBusy = false
            }
          }
        }
      },
      async getAssetWorkflowStatus (token, assetId) {
        let response = await fetch(process.env.VUE_APP_WORKFLOW_API_ENDPOINT+'workflow/execution/asset/'+assetId, {
            method: 'get',
            headers: {
              'Authorization': token
          }
        })
        let result = await response.json()
        return result
      },
      async getAssetThumbNail (token, bucket, s3Key) {
        const data = { "S3Bucket": bucket, "S3Key": s3Key }
        let response = await fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT + '/download', {
            method: 'POST',
            mode: 'cors',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': token
            },
            body: JSON.stringify(data)
          })
        if (response.status === 200) {
          let result = await response.text()
          return result
        }
        else {
          this.showDataplaneAlert = true
        }
      },
      async getAssetInformation (token, assetId) {
        let response = await fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT+'/metadata/'+assetId, {
            method: 'get',
            headers: {
              'Authorization': token
          }
        })
        if (response.status === 200) {
          let result = await response.json()
          return result
        }
        else {
          this.showDataplaneAlert = true
        }
      },
      async fetchAssets (token) {
        let response = await fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT+'/metadata', {
            method: 'get',
            headers: {
              'Authorization': token
          }
        })
        if (response.status === 200) {
          let result = await response.json()
          return result
        }
        else {
          this.showDataplaneAlert = true
        }
      },
      async getAccessToken () {
          let response = await this.$Amplify.Auth.currentSession()
          let result = await response.getIdToken().getJwtToken()
          return result
      },
      async pushAssetsToTable(assets) {
        let token = await this.getAccessToken()
        for (var i = 0, len = assets.length; i < len; i++) {
          // check if from search collection or retrieve and format
          var assetId;
          if (typeof assets[i] === 'object') {
            assetId = assets[i].asset_id
            }
          else {
            assetId = assets[i]
          }
          let assetInfo = await this.getAssetInformation(token, assetId)
          let created = new Date(0);
          created.setUTCSeconds(assetInfo.results.Created)
          let bucket = assetInfo.results.S3Bucket
          let s3Key = assetInfo.results.S3Key
          let s3Uri = 's3://'+ bucket+'/'+ s3Key
          let filename = s3Key.split("/").pop()
          let thumbnailS3Key = 'private/assets/' + assetId + '/input/' + filename
          if (filename.substring(filename.lastIndexOf(".")) === ".mp4") {
              thumbnailS3Key = 'private/assets/' + assetId + '/' + filename.substring(0, filename.lastIndexOf(".")) + '_thumbnail.0000001.jpg'
          }
          let thumbnail = await this.getAssetThumbNail(token, bucket, thumbnailS3Key)
          let workflowStatus = await this.getAssetWorkflowStatus(token, assetId)
          this.asset_list.push({
            asset_id: assetId,
            Created: created.toLocaleDateString(),
            Filename: filename,
            status: workflowStatus[0].Status,
            s3_uri: s3Uri,
            signedUrl: thumbnail,
            thumbnailID: '_' + assetId,
            Thumbnail: '',
            Actions: 'Run'
            })
        }
      },
      async retrieveAndFormatAsssets () {
        let token = await this.getAccessToken()
        let data = await this.fetchAssets(token)
        let assets = data.assets
        if (assets.length === 0) {
          this.noAssets = true
          this.noSearchResults = false
          this.isBusy = false;
        }
        else {
          this.noAssets = false
          this.pushAssetsToTable(assets)
          this.totalRows = this.asset_list.length
          this.isBusy = false
        }
      }
    }
  }
</script>

<style>
  td {
    vertical-align: middle;
  }
  .headerTextBackground {
    background-color: #191918;
    max-width: 100%;
    height: auto;
    padding-bottom: 1%;
  }
  .resultsTable {
    padding-top: 1%;
  }
  h1 {
    color: #ED900E;
  }
  a {
    color: #ED900E;
  }
  .tagline {
    color: white
  }
  .btn-orange {
    color: #ED900E
  }
  .btn-red {
    color: red
  }
  .tableWordWrap {
    white-space:normal;
    word-break:break-all;
    overflow: hidden;
    text-overflow:ellipsis;
  }
</style>
