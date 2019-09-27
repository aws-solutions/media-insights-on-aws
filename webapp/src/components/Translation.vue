<template>
  <div>
    <div
      v-if="isBusy"
      class="wrapper"
    >
      <b-spinner
        variant="secondary"
        label="Loading..."
      />
      <p class="text-muted">
        (Loading...)
      </p>
    </div>
    <div
      v-else
      class="wrapper"
    >
      <label>Source Language:</label> {{ source_language }}<br>
      <label>Target Language:</label> {{ target_language }}<br>
      {{ translated_text }}
    </div>
  </div>
</template>

<script>
export default {
  name: "Translation",
  data() {
    return {
      translated_text: "",
      source_language: "",
      target_language: "",
      isBusy: false,
      operator: "translation"
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
      this.translated_text = "",
      this.source_language = "",
      this.target_language = ""
    },
  methods: {
    fetchAssetData () {
      const vm = this;
      fetch(process.env.VUE_APP_ELASTICSEARCH_ENDPOINT+'/_search?q=AssetId:'+this.$route.params.asset_id+' _index:mietranslation&default_operator=AND&size=10000', {
        method: 'get'
      }).then(response =>
        response.json().then(data => ({
            data: data,
            status: response.status
          })
        ).then(res => {
          res.data.hits.hits.forEach(function (item) {
            vm.translated_text = item._source.TranslatedText
            vm.source_language = item._source.SourceLanguageCode
            vm.target_language = item._source.TargetLanguageCode
          });
          vm.isBusy = false
        })
      );
    }
  }
}
</script>
