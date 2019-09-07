<template>
  <div>
    <div class="wrapper">
      <b-nav-form>
        <b-form-input size="sm" class="mr-sm-2" placeholder="Search"></b-form-input>
      </b-nav-form>
    Confidence Threshold<br>
    <input @input="updateConfidence" type="range" value="90" min="55" max="99" step="1">
    {{ Confidence }}%
    </div>
    <div class="wrapper">
      <template v-for="item in confidence_filter">
        <b-table striped hover :items="item" :fields="fields" :sort-by.sync="sortBy"
                 :sort-desc.sync="sortDesc"></b-table>
      </template>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
    name: "LabelTimeline",
    data() {
      return {
        sortBy: 'Timestamp',
        sortDesc: false,
        fields: [
          { key: 'Timestamp', sortable: true },
          { key: 'Name', sortable: true },
          { key: 'Confidence', sortable: false },
        ],
      }
    },
    methods: {
      updateConfidence (e) {
        this.$store.commit('updateConfidence', e.target.value, 'labeldetection')
      }
    },
    computed: {
      ...mapState(['es_data', 'Confidence']),
      confidence_filter() {
        // Clone the master dataset
        var es_data = this.es_data;
        var timeline_table = {
          label: []
        };
        es_data.forEach(function (record) {
            timeline_table.label.push({'Timestamp': record.Timestamp/1000+'s', 'Name': record.Label, 'Confidence': Math.round(record.Confidence)+'%'})
        });
        return timeline_table
      }
    }
}
</script>
