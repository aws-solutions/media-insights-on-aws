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
import awsconfig from "@/aws-exports";

Amplify.configure(awsconfig);

Vue.config.productionTip = false

var marked = require('marked');

Vue.mixin({
  methods: {
    marked: function (input) {
      return marked(input);
    }
  }
});

Vue.use(AmplifyPlugin, AmplifyModules);
Vue.use(BootstrapVue)

new Vue({
  router,
  store,
  render: h => h(App),
}).$mount('#app')
