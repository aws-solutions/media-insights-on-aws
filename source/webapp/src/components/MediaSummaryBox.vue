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
        <div
          v-if="isBusy === false"
          class="wrapper"
        >
          <b-row>
            <b-col>
              <div v-if="duration !== 'undefined'">
                <label>Video duration:</label>
                {{ duration }}
              </div>
              <div v-if="format !== 'undefined'">
                <label>Video format:</label>
                {{ format }}
              </div>
              <div v-if="file_size !== 'undefined'">
                <label>Video file size:</label>
                {{ file_size }} MB
              </div>
              <div v-if="overall_bit_rate !== 'undefined'">
                <label>Video bit rate:</label>
                {{ overall_bit_rate }} Mbps
              </div>
              <div v-if="frame_rate !== 'undefined'">
                <label>Video frame rate:</label>
                {{ frame_rate }} fps
              </div>
              <div v-if="width !== 'undefined' && height !== 'undefined' ">
                <label>Video resolution:</label>
                {{ width }} x {{ height }}
              </div>
            </b-col>
            <b-col>
              <div v-if="other_bit_rate !== 'undefined'">
                <label>Audio bit rate:</label>
                {{ other_bit_rate }}
              </div>
              <div v-if="other_sampling_rate !== 'undefined'">
                <label>Audio sampling rate:</label>
                {{ other_sampling_rate }}
              </div>
              <div v-if="other_language !== 'undefined'">
                <label>Audio Language:</label>
                {{ other_language }}
              </div>
              <div v-if="encoded_date !== 'undefined'">
                <label>Encoded date:</label>
                {{ encoded_date }}
              </div>
            </b-col>
          </b-row>
        </div>
      </b-col>
    </b-row>
  </b-container>
</template>

<script>
  export default {
    name: 'MediaSummary',
    props: ['s3Uri','filename','videoUrl'],
    data () {
      return {
        duration: "undefined",
        elasticsearch_data: [],
        mediainfo_data: [],
        format: "undefined",
        file_size: "undefined",
        overall_bit_rate: "undefined",
        frame_rate: "undefined",
        width: "undefined",
        height: "undefined",
        other_bit_rate: "undefined",
        other_sampling_rate: "undefined",
        other_language: "undefined",
        encoded_date: "undefined",
        isBusy: false,
      }
    },
    deactivated: function () {
      this.lineChart = Object
    },
    mounted: function () {
      this.fetchAssetData();
    },
    beforeDestroy: function () {
    },
    methods: {
      async fetchAssetData () {
        this.isBusy = true;
        let query = 'AssetId:'+this.$route.params.asset_id+' Operator:mediainfo';
        let apiName = 'mieElasticsearch';
        let path = '/_search';
        let apiParams = {
          headers: {'Content-Type': 'application/json'},
          queryStringParameters: {'q': query, 'default_operator': 'AND', 'size': 10000}
        };
        let response = await this.$Amplify.API.get(apiName, path, apiParams);
        if (!response) {
          this.showElasticSearchAlert = true
        } else {
          let es_data = [];
          let result = await response;
          let data = result.hits.hits;
          for (let i = 0, len = data.length; i < len; i++) {
            es_data.push(data[i]._source);
          }
          this.elasticsearch_data = JSON.parse(JSON.stringify(es_data));
          let track_data = {"General": undefined, "Video": undefined, "Audio": undefined};
          track_data["General"] = this.elasticsearch_data.filter(x => x.track_type === "General");
          track_data["Video"] = this.elasticsearch_data.filter(x => x.track_type === "Video");
          track_data["Audio"] = this.elasticsearch_data.filter(x => x.track_type === "Audio");
          if ("duration" in track_data["General"][0]) {
            let seconds = track_data["General"][0].duration / 1000;
            if (seconds >= 3600) {
              this.duration = new Date(seconds * 1000).toISOString().substr(11, 8);
            } else {
              // drop hours portion if time is less than 1 hour
              this.duration = new Date(seconds * 1000).toISOString().substr(14, 5);
            }
          }
          if ("format" in track_data["General"][0]) {
            this.format = track_data["General"][0].format;
          }
          if ("file_size" in track_data["General"][0]) {
            this.file_size = (track_data["General"][0].file_size / 1000 / 1000).toFixed(2);
          }
          if ("overall_bit_rate" in track_data["General"][0]) {
            this.overall_bit_rate = track_data["General"][0].overall_bit_rate;
          }
          if ("frame_rate" in track_data["General"][0]) {
            this.frame_rate = track_data["General"][0].frame_rate;
          }
          if ("width" in track_data["Video"][0]) {
            this.width = track_data["Video"][0].width;
          }
          if ("height" in track_data["Video"][0]) {
            this.height = track_data["Video"][0].height;
          }
          if ("other_bit_rate" in track_data["Audio"][0]) {
            this.other_bit_rate = track_data["Audio"][0].other_bit_rate[0];
          }
          if ("other_sampling_rate" in track_data["Audio"][0]) {
            this.other_sampling_rate = track_data["Audio"][0].other_sampling_rate[0];
          }
          if ("other_language" in track_data["Audio"][0]) {
            this.other_language = track_data["Audio"][0].other_language[0];
          }
          if ("encoded_date" in track_data["Audio"][0]) {
            this.encoded_date = track_data["Audio"][0].encoded_date;
          }
          this.isBusy = false
        }
      }
    }
  }
</script>

<style>

</style>
