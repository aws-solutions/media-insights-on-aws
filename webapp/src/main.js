import Vue from 'vue'
import BootstrapVue from 'bootstrap-vue'

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import 'dropzone/dist/min/dropzone.min.css'

import App from './App.vue'
import store from './store'
import router from './router.js'
import Amplify, * as AmplifyModules from "aws-amplify";
import { AmplifyPlugin } from "aws-amplify-vue";

const getRuntimeConfig = async () => {
  const runtimeConfig = await fetch('/runtimeConfig.json');
  return await runtimeConfig.json()
}

getRuntimeConfig().then(function(json) {
  const awsconfig = {
    Auth: {
      region: json.AWS_REGION,
      userPoolId: json.USER_POOL_ID,
      userPoolWebClientId: json.USER_POOL_CLIENT_ID,
      identityPoolId: json.IDENTITY_POOL_ID
    },
    API: {
      endpoints: [
        {
          name: "mieElasticsearch",
          endpoint: json.ELASTICSEARCH_ENDPOINT,
          service: "es",
          region: json.AWS_REGION
        }
      ]
    }
  };
  console.log("Runtime config: " + JSON.stringify(json))
  Amplify.configure(awsconfig);
  Vue.config.productionTip = false
  var marked = require('marked');
  Vue.mixin({
    methods: {
      marked: function (input) {
        return marked(input);
      }
    },
    data() {
      return {
        // Distribute the runtime config into every Vue component
        runtimeConfig: json
      }
    },
  });

  Vue.use(AmplifyPlugin, AmplifyModules);
  Vue.use(BootstrapVue)

  new Vue({
    router,
    store,
    render: h => h(App),
  }).$mount('#app')
});
