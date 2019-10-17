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
            <div
              v-for="workflow in workflows"
              :key="workflow"
            >
              <input
                v-model="selected_workflow"
                type="radio"
                name="selected_workflow"
                :value="workflow"
              > {{ workflow }}
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
    components: {
      Header
    },
    data: function () {
      return {
        workflows: [],
        selected_workflow: ""
      }
    },
    mounted: function () {
      this.fetchWorkflows();
    },
    methods: {
      async fetchWorkflows() {
      const token = await this.$Amplify.Auth.currentSession().then(data =>{
        var accessToken = data.getIdToken().getJwtToken()
        return accessToken
        })
        let workflow_list = [];
        fetch(process.env.VUE_APP_WORKFLOW_API_ENDPOINT+'/workflow', {
          method: 'get',
          headers: {
            'Authorization': token
          }
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
    }
  }
</script>

<style scoped>

</style>
