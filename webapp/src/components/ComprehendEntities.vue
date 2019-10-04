<template>
  <div>
    <div class="wrapper">
      Confidence Threshold<br>
      <input
        type="range"
        value="90"
        min="55"
        max="99"
        step="1"
        @click="updateConfidence"
      >
      {{ Confidence }}%<br>
    </div>
    <div
      v-if="isBusy"
      class="wrapper"
    >
      <Loading />
    </div>
    <div class="wrapper">
      <b-table
        responsive
        fixed
        :items="entities"
        :fields="fields"
        :sort-by="sortBy"
      >
        <template v-slot:cell(Confidence)="data">
          {{ (data.item.Confidence * 1).toFixed(2) }}
        </template>
      </b-table>
    </div>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue'
import { mapState } from 'vuex'

export default {
  name: "Entities",
  components: {
    Loading
    },
  data() {
    return {
      Confidence: 90,
      sortBy: "BeginOffset",
      fields: [
        { key: 'EntityText', sortable: true },
        { key: 'EntityType', sortable: true },
        { key: 'Confidence', sortable: true },
        { key: 'BeginOffset', sortable: true },
        { key: 'EndOffset', sortable: true },
      ],
      entities: [],
      isBusy: false,
      operator: "entities"
    }
  },
  computed: {
    ...mapState(['player']),
  },
  deactivated: function () {
    console.log('deactivated component:', this.operator)
  },
  activated: function () {
    console.log('activated component:', this.operator)
    this.fetchAssetData();
  },
  beforeDestroy: function () {
    this.entities = []
  },
  methods: {
    updateConfidence (event) {
      this.isBusy = true;
      this.entities = [];
      this.Confidence = event.target.value;
      this.fetchAssetData()
    },
    fetchAssetData () {
      const vm = this;
      fetch(process.env.VUE_APP_ELASTICSEARCH_ENDPOINT+'/_search?q=AssetId:'+this.$route.params.asset_id+' Confidence:>'+this.Confidence+' _index:mieentities&default_operator=AND&size=100', {
        method: 'get'
      }).then(response =>
        response.json().then(data => ({
            data: data,
            status: response.status
          })
        ).then(res => {
          res.data.hits.hits.forEach(function (item) {
            vm.entities.push({ "EntityText": item._source.EntityText, "EntityType": item._source.EntityType, "Confidence": item._source.Confidence, "BeginOffset": item._source.BeginOffset, "EndOffset": item._source.EndOffset})
          });
          vm.isBusy = false
        })
      );
    }
  }
}
</script>
