<template>
  <div>
    <div v-if="this.isBusy" class="wrapper">
      <b-spinner variant="secondary" label="Loading..."></b-spinner>
      <p class="text-muted">(Loading...)</p></div>
    <div v-else class="wrapper">
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
      operator: "transcript"
    }
  },
  methods: {
    fetchAssetData () {
      const vm = this;
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
    }
}
</script>
