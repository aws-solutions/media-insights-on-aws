<template>
  <div>
    <div v-if="isBusy">
      <b-spinner
        variant="secondary"
        label="Loading..."
      />
      <p class="text-muted">
        (Loading...)
      </p>
    </div>
    <div v-else>
      <div v-if="isProfane">
        <span style="color:red">WARNING: Transcript contains potentially offensive words.</span>
        <br>
        <br>
      </div>
      {{ transcript }}
    </div>
  </div>
</template>

<script>
export default {
  name: "Transcript",
  data() {
    return {
      transcript: "",
      isBusy: false,
      operator: "transcript",
    }
  },
  computed: {
    isProfane() {
      var Filter = require('bad-words');
      var profanityFilter = new Filter({ placeHolder: '_' });
      var result = profanityFilter.isProfane(this.transcript);
      return result
    },
  },
  deactivated: function () {
    console.log('deactivated component:', this.operator)
  },
  activated: function () {
    console.log('activated component:', this.operator)
    this.fetchAssetData();
  },
  beforeDestroy: function () {
      this.transcript = ''
  },
  methods: {
    fetchAssetData () {
      const vm = this;
      vm.isBusy = true;
      fetch(process.env.VUE_APP_ELASTICSEARCH_ENDPOINT+'/_search?q=AssetId:'+this.$route.params.asset_id+' _index:mietranscript&default_operator=AND&size=10000', {
        method: 'get'
      }).then(response =>
        response.json().then(data => ({
            data: data,
            status: response.status
          })
        ).then(res => {
          res.data.hits.hits.forEach(function (item) {
            vm.transcript = item._source.transcript
          });
          vm.isBusy = false
        })
      );
    }
  }
}
</script>
