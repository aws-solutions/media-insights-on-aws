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
          fade
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
                    <template v-slot:cell(Created)="data">
                      {{ data.item.Created.toLocaleDateString() }}<br>
                      {{ data.item.Created.toLocaleTimeString() }}
                    </template>
                    <template v-slot:cell(status)="data">
                      <!-- open link in new tab -->
                      <a href="" @click.stop.prevent="openWindow(data.item.state_machine_console_link)">{{ data.item.status }}</a>
                    </template>
                    <template v-slot:cell(Actions)="data">
                      <b-button
                        variant="orange"
                        :href="(`/analysis/${data.item.asset_id}`)"
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
        showDeletedAlert: 0,
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
    computed: {
      totalRows() {
        return this.asset_list.length
      }
    },
    created: function () {
      this.isBusy = true;
      this.retrieveAndFormatAsssets()
    },
    methods: {
      openWindow: function (url) {
        window.open(url);
      },
      async deleteAsset(asset_id) {
        let token = await this.getAccessToken();
        let response = await fetch(this.DATAPLANE_API_ENDPOINT+'/metadata/'+asset_id, {
          method: 'delete',
          headers: {
            'Authorization': token
          }
        });
        if (response.status === 200) {
            this.showDeletedAlert = 5;
            this.asset_list = [];
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
            };
            let response = await this.$Amplify.API.post(apiName, path, apiParams);
            if (!response) {
              this.showElasticSearchAlert = true
            }
            else {
              this.noAssets = false;
              return await response;
        }
      },
      async searchCollection () {
          this.noSearchResults = false;
          this.isBusy = true;
          let query = this.user_defined_query;
          // if search is empty string then get asset list from dataplane instead of Elasticsearch.
          if (query === "") {
            this.showElasticSearchAlert = false;
            this.asset_list = [];
            this.retrieveAndFormatAsssets();
            this.isBusy = false;
          }
          else {
            // Get the list of assets that contain metadata matching the user-specified search query.
            let elasticData = await this.elasticsearchQuery(query);
            if (elasticData.hits.total === 0) {
              // the search returned no data
              this.asset_list = [];
              this.noSearchResults = true;
              this.isBusy = false;
            }
            else {
              let assets = [];
              this.asset_list = [];
              this.noSearchResults = false;
              let token = await this.getAccessToken();
              let buckets = elasticData.aggregations.distinct_assets.buckets;
              for (var i = 0, len = buckets.length; i < len; i++) {
                let assetId = buckets[i].key;
                let assetInfo = await this.getAssetInformation(token, assetId);
                if (assetInfo !== null) {
                  assets.push(assetInfo)
                }
            }
            if (assets.length === 0) {
              this.noSearchResults = true;
              this.isBusy = false
            }
            else {
              this.pushAssetsToTable(assets);
              this.isBusy = false
            }
          }
        }
      },
      async getAssetWorkflowStatus (token, assetId) {
        let response = await fetch(this.WORKFLOW_API_ENDPOINT+'workflow/execution/asset/'+assetId, {
            method: 'get',
            headers: {
              'Authorization': token
          }
        });
        return await response.json();
      },
      async getAssetThumbnail (token, bucket, s3Key) {
        const data = { "S3Bucket": bucket, "S3Key": s3Key };
        let response = await fetch(this.DATAPLANE_API_ENDPOINT + '/download', {
            method: 'POST',
            mode: 'cors',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': token
            },
            body: JSON.stringify(data)
          });
        if (response.status === 200) {
          return await response.text();
        }
        else {
          this.showDataplaneAlert = true
        }
      },
      async getAssetInformation (token, assetId) {
        let response = await fetch(this.DATAPLANE_API_ENDPOINT+'/metadata/'+assetId, {
            method: 'get',
            headers: {
              'Authorization': token
          }
        });
        if (response.status === 200) {
          return await response.json();
        }
        else {
          this.showDataplaneAlert = true
        }
      },
      async fetchAssets (token) {
        let response = await fetch(this.DATAPLANE_API_ENDPOINT+'/metadata', {
            method: 'get',
            headers: {
              'Authorization': token
          }
        });
        if (response.status === 200) {
          return await response.json();
        }
        else {
          this.showDataplaneAlert = true
        }
      },
      async getAccessToken () {
          let response = await this.$Amplify.Auth.currentSession();
          return await response.getIdToken().getJwtToken();
      },
      async pushAssetsToTable(assets) {
        let token = await this.getAccessToken();
        for (var i = 0, len = assets.length; i < len; i++) {
          var assetId;
          if (typeof assets[i] === 'object') {
            // If the asset list is coming from Elasticsearch, we get the assetId like this:
            assetId = assets[i].asset_id
          } else {
            // If the asset list is coming from the dataplaneapi, we get the assetId like this:
            assetId = assets[i]
          }
          // Invoke an asynchronous task to add assets to the table in parallel so the table updates
          // as fast as possible. For large media collections this may take several seconds.
          this.pushAssetToTable(assetId, token)
        }
      },
      async pushAssetToTable (assetId, token) {
        let assetInfo = await this.getAssetInformation(token, assetId);
        let created = new Date(0);
        created.setUTCSeconds(assetInfo.results.Created);
        let bucket = assetInfo.results.S3Bucket;
        let s3Key = assetInfo.results.S3Key;
        let s3Uri = 's3://' + bucket + '/' + s3Key;
        let filename = s3Key.split("/").pop();
        // The thumbnail is created by Media Convert, see:
        // source/operators/thumbnail/start_thumbnail.py
        let thumbnailS3Key = 'private/assets/' + assetId + '/' + filename.substring(0, filename.lastIndexOf(".")) + '_thumbnail.0000001.jpg';
        // If it's an image then Media Convert won't create a thumbnail.
        // In that case we use the uploaded image as the thumbnail.
        let supported_image_types = [".jpg", ".jpeg", ".tif", ".tiff", ".png", ".apng", ".gif", ".bmp", ".svg"];
        let media_type = filename.substring(filename.lastIndexOf(".")).toLowerCase();
        if (supported_image_types.includes(media_type)) {
          // use the uploaded image as a thumbnail
          thumbnailS3Key = 'private/assets/' + assetId + '/input/' + filename;
        }
        let [thumbnail, workflowStatus] = await Promise.all([this.getAssetThumbnail(token, bucket, thumbnailS3Key), this.getAssetWorkflowStatus(token, assetId)]);
        if (workflowStatus[0] && thumbnail)
        {
          this.asset_list.push({
            asset_id: assetId,
            Created: created,
            Filename: filename,
            status: workflowStatus[0].Status,
            state_machine_console_link: "https://" + this.AWS_REGION + ".console.aws.amazon.com/states/home?region=" + this.AWS_REGION + "#/executions/details/" + workflowStatus[0].StateMachineExecutionArn,
            s3_uri: s3Uri,
            signedUrl: thumbnail,
            thumbnailID: '_' + assetId,
            Thumbnail: '',
            Actions: 'Run'
          })
        }
      },

      async retrieveAndFormatAsssets () {
        let token = await this.getAccessToken();
        let data = await this.fetchAssets(token);
        let assets = data.assets;
        if (assets.length === 0) {
          this.noAssets = true;
          this.noSearchResults = false;
          this.isBusy = false;
        }
        else {
          this.noAssets = false;
          this.pushAssetsToTable(assets);
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
