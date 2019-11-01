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
            href="https://w.amazon.com/bin/view/Media_insights_engine/#overview"
            disabled
          >
            Help
          </b-nav-item>
          <b-nav-item
            v-if="signedIn"
            @click="signOut()"
          >
            <p id="signOutBtn">
              Sign Out
            </p>
          </b-nav-item>
        </b-navbar-nav>
      </b-collapse>
    </b-navbar>
    <br>
  </div>
</template>

<script>
import { AmplifyEventBus } from "aws-amplify-vue";

export default {
  name: 'Header',
  props: ['isCollectionActive', 'isUploadActive'],
  data() {
    return {
      elasticsearch_endpoint: process.env.VUE_APP_ELASTICSEARCH_ENDPOINT,
      signedIn: false
    }
  },
  async beforeCreate() {
    try {
      await this.$Amplify.Auth.currentAuthenticatedUser();
      this.signedIn = true;
    } catch (err) {
      this.signedIn = false;
    }
    AmplifyEventBus.$on("authState", info => {
      this.signedIn = info === "signedIn";
    });
  },
  async mounted() {
    AmplifyEventBus.$on("authState", info => {
      this.signedIn = info === "signedOut";
      this.$router.push({name: 'Login'})
    });
  },
  methods: {
    signOut() {
      this.$Amplify.Auth.signOut()
          .then(() => this.$router.push({name: "Login"}))
          .catch(err => console.log(err));
    }
  }
}
</script>

<style>

#signOutBtn {
color: #ED900E;
}

</style>
