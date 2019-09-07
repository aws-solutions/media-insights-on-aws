import Vue from 'vue'
import VueRouter from 'vue-router'
import Analysis from '@/views/Analysis.vue'
import Upload from '@/views/UploadToAWSS3.vue'
import Run from '@/views/Run.vue'
import Collection from '@/views/Collection.vue'

Vue.use(VueRouter)

export default new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/collection',
      name: 'collection',
      component: Collection,
      alias: '/'
    },
    {
      path: '/upload',
      name: 'upload',
      component: Upload
    },
    {
      path: '/analysis/:asset_id',
      name: 'analysis',
      component: Analysis
    },
    {
      path: '/run/:asset_id',
      name: 'run',
      component: Run
    }
  ]
})
