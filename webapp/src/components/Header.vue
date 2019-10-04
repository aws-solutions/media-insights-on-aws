<template>
  <div>
    <b-navbar
      toggleable="lg"
      type="dark"
      variant="dark"
    >
      <b-navbar-brand to="/">
        Media Insights Engine
      </b-navbar-brand>
      <b-navbar-toggle target="nav-collapse" />

      <b-collapse
        id="nav-collapse"
        is-nav
      >
        <!-- Right aligned nav items -->
        <b-navbar-nav class="ml-auto">
          <b-nav-item
            to="/upload"
            :class="{ active: isUploadActive }"
          >
            Upload
          </b-nav-item>
          <b-nav-item
            to="/collection"
            :class="{ active: isCollectionActive }"
          >
            Collection
          </b-nav-item>
          <b-nav-item
            :href="`${elasticsearch_endpoint}/_plugin/kibana/`"
            target="_blank"
          >
            Analytics
          </b-nav-item>
          <b-nav-item
            href="https://w.amazon.com/bin/view/Media_insights_engine/#overview"
            disabled
          >
            Help
          </b-nav-item>
        </b-navbar-nav>
      </b-collapse>
    </b-navbar>
    <br>
  </div>
</template>

<script>
export default {
  name: 'Header',
  props: ['isCollectionActive', 'isUploadActive'],
  data() {
    return {
      elasticsearch_endpoint: process.env.VUE_APP_ELASTICSEARCH_ENDPOINT
    }
  }
}
</script>

<style scoped>

</style>
