<template>
  <div>
    <Header />
    <b-container>
      <b-row>
        <b-col>
          <div>
            Selected AssetID:
          </div>
        </b-col>
        <b-col>
          <div>
            Select a workflow to run:
            <div v-for="workflow in workflows" v-bind:key="workflow">
              <input type="radio" v-model="selected_workflow" name="selected_workflow" :value="workflow"> {{ workflow }}
            </div>
            <br>
            You chose {{ selected_workflow }}
          </div>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
  import Header from '@/components/Header.vue'

  export default {
    name: "Run",
    data: function () {
      return {
        workflows: [],
        selected_workflow: ""
      }
    },
    methods: {
      fetchWorkflows() {
        let workflow_list = [];
        fetch(process.env.VUE_APP_WORKFLOW_API_ENDPOINT+'/workflow', {
          method: 'get'
        }).then(response =>
          response.json().then(data => ({
              data: data,
            })
          ).then(res => {
            res.data.forEach(function (item) {
              workflow_list.push(item.Name)
            })
          })
        );
        this.workflows = workflow_list;
      },
    },
    mounted: function () {
      this.fetchWorkflows();
    },
    components: {
      Header
    }
  }
</script>

<style scoped>

</style>
