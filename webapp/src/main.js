import Vue from 'vue'
import BootstrapVue from 'bootstrap-vue'

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import '@/dist/min/dropzone.min.css'

import App from './App.vue'
import store from './store'
import router from './router.js'

Vue.config.productionTip = false

var marked = require('marked');

Vue.mixin({
  methods: {
    marked: function (input) {
      return marked(input);
    }
  }
});

Vue.use(BootstrapVue)

new Vue({
  router,
  store,
  render: h => h(App),
}).$mount('#app')
