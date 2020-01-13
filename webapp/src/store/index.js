import Vue from 'vue'
import Vuex from 'vuex'
import state from './state'
import mutations from './mutations'
import actions from './actions'
import createPersistedState from "vuex-persistedstate";

Vue.use(Vuex);

export default new Vuex.Store({
  state,
  mutations,
  actions,
  plugins: [createPersistedState({
    paths: ['execution_history']
  })]
})
