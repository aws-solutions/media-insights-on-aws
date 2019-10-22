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
          Elasticsearch server denied access. Please check its access policy.
        </b-alert>
        <b-alert
          v-model="showDataplaneAlert"
          variant="danger"
          dismissible
        >
          Failed to connect to dataplane. Please check access control policy in API Gateway.
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
              @keyup.enter="elasticsearchQuery"
            >
          </b-col>
          <b-col sm="1">
            <b-button
              size="lg"
              @click="elasticsearchQuery"
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
        totalRows: 1,
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
      this.retrieveAndFormatAsssets()
    },
    methods: {
      async deleteAsset(asset_id) {
        const token = await this.$Amplify.Auth.currentSession().then(data =>{
          var accessToken = data.getIdToken().getJwtToken()
          return accessToken
        })
        const vm = this;
        console.log("Deleting asset_id " + asset_id)
        fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT+'/metadata/'+asset_id, {
          method: 'delete',
          headers: {
            'Authorization': token
          }
        }).then(response => {
          response.text().then(data => ({
              data: data,
            })
          ).then(res => {
            console.log(res.data);
            vm.asset_list = [];
            vm.fetchAssetList();
          });
        })
      },
      async elasticsearchQuery() {
        const token = await this.$Amplify.Auth.currentSession().then(data =>{
          var accessToken = data.getIdToken().getJwtToken()
          return accessToken
        })
        // This function gets the list of assets that contain metadata matching a user-specified search query.
        // Then it updates the display to only show those matching assets.
        var vm = this;
        vm.isBusy = true;
        var user_defined_query = vm.user_defined_query;
        // if search is empty string then get asset list from dataplane instead of Elasticsearch.
        if (user_defined_query === "") {
          this.showElasticSearchAlert = false;
          vm.asset_list = [];
          this.fetchAssetList();
          return;
        }
        // Get the list of assets that contain metadata matching the user-specified search query.
        var data = {
          aggs: {
            distinct_assets: {
              terms: {
                field: "AssetId.keyword",
                size: 10000
              }
            }
          }
        };
        fetch(process.env.VUE_APP_ELASTICSEARCH_ENDPOINT+'/_search?q='+user_defined_query+'&_source=AssetId', {
          method: 'post',
          body: JSON.stringify(data),
          headers: {'Content-Type': 'application/json'}
        }).then(response =>
          response.json().then(data => ({
              data: data,
              status: response.status
            })
          ).then(res => {
            if (res.status == 403) {
              this.showElasticSearchAlert = true
            }
            var filtered_asset_list = [];
            if (!res.data.aggregations) {
              // the search returned no data
              vm.asset_list = []
              vm.isBusy = false;
            } else {
              res.data.aggregations.distinct_assets.buckets.forEach( function (item) {
                // Display only the matching assets in the collection view.
                var assetid = item.key
                fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT+'/metadata/'+assetid, {
                  method: 'get',
                  headers: {
                    'Authorization': token
                  }
                }).then(response2 => {
                  response2.json().then(data2 => ({
                      data2: data2,
                    })
                  ).then(res2 => {
                    const datetime = new Date(0);
                    datetime.setUTCSeconds(res2.data2.results.Created);
                    var s3_uri = 's3://'+res2.data2.results.S3Bucket+'/'+res2.data2.results.S3Key;
                    var filename = res2.data2.results.S3Key.split("/").pop()
                    var thumbnail_s3_key = 'private/assets/' + assetid + '/input/' + filename;
                    if (filename.substring(filename.lastIndexOf(".")) === ".mp4") {
                      thumbnail_s3_key = 'private/assets/' + assetid + '/' + filename.substring(0, filename.lastIndexOf(".")) + '_thumbnail.0000001.jpg';
                    }
                    // get URL to thumbnail file in S3
                    fetch(process.env.VUE_APP_DATAPLANE_API_ENDPOINT + '/download', {
                      method: 'POST',
                      mode: 'cors',
                      headers: {
                        'Content-Type': 'application/json',
                        'Authorization': token
                      },
                      body: JSON.stringify({"S3Bucket": res2.data2.results.S3Bucket, "S3Key": thumbnail_s3_key})
                    }).then(response =>
                      response.text()).then((data) => {

                      // get workflow status for each asset
                      fetch(process.env.VUE_APP_WORKFLOW_API_ENDPOINT+'workflow/execution/asset/'+assetid, {
                        method: 'get',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': token
                        },
                      }).then(response =>
                        response.json().then(data => ({
                            data: data,
                            status: response.status
                          })
                        ).then(res => {
                          if (res.status != 200) {
                            console.log("ERROR: Failed to get workflow status")
                          } else {
                            var status = res.data[0].Status;
                            const signed_url = data;
                            // media_type = res2.data2.results.S3Key.split('.').pop();
                            // console.log('media type: ' + media_type)
                            vm.asset_list.push({
                              asset_id: assetid,
                              Created: datetime.toISOString(),
                              Filename: filename,
                              status: status,
                              s3_uri: s3_uri,
                              signedUrl: signed_url,
                              thumbnailID: '_' + assetid,
                              Thumbnail: '',
                              Actions: 'Run'
                            })
                          }
                        })
                      );
                    });
                  })
                });
              });
              vm.asset_list = filtered_asset_list;
              // Trigger pagination to update the number of buttons/pages
              vm.totalRows = vm.asset_list.length;
              vm.isBusy = false;
            }
          })
        )
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
        console.log(data)
        console.log('getting thumbnail')
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
      pushAssetToTable(assetId, created, filename, status, s3_uri, signed_url, action) {
        this.asset_list.push({
          asset_id: assetId,
          Created: created.toLocaleDateString(),
          Filename: filename,
          status: status,
          s3_uri: s3_uri,
          signedUrl: signed_url,
          thumbnailID: '_' + assetId,
          Thumbnail: '',
          Actions: action
        })
      },
      async retrieveAndFormatAsssets () {
        let token = await this.getAccessToken()
        let data = await this.fetchAssets(token)
        let assets = data.assets
        if (assets.length === 0) {
          vm.isBusy = false;
          }
        for (var i = 0, len = assets.length; i < len; i++) {
            let assetId = assets[i]
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
            this.pushAssetToTable(assetId, created, filename, workflowStatus[0].Status, s3Uri, thumbnail, 'Run')
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
