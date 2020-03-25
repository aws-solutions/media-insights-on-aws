<template>
  <div>
    <amplify-authenticator></amplify-authenticator>
  </div>
</template>

<script>
//-----------------------------------------------------------//
// Hack to work around a bug in amplify-authenticator, which makes it so it
// doesn't notice if a username is autofilled rather than being typed in.
// This work around enables the 1password browser plugin to autofill
// username and password.
//
// See https://github.com/aws-amplify/amplify-js/issues/4374
//
// This hack can be removed once the issue is resolved.
function patchSignIn () {
  // monkey-patch the UsernameField component, and add a watcher to make it properly emit a changed
  // event when the username field changes
  let usernameComponent = Vue.component('amplify-username-field');
  let watches = usernameComponent.options.watch = usernameComponent.options.watch || {};
  watches.username = function () {
    this.usernameChanged()
  };
  watches.email = function () {
    this.emailChanged()
  }
}
import Vue from 'vue'
patchSignIn();
//-----------------------------------------------------------//

import { AmplifyEventBus } from "aws-amplify-vue";
export default {
  name: "Login",
  data() {
    return {};
  },
  mounted() {
    AmplifyEventBus.$on("authState", eventInfo => {
      if (eventInfo === "signedIn") {
        this.$router.push({ name: "collection" });
      } else if (eventInfo === "signedOut") {
        this.$router.push({ name: "Login" });
      }
    });
  },
  created() {
    this.getLoginStatus()
  },
  methods: {
    getLoginStatus () {
      this.$Amplify.Auth.currentSession().then(data => {
        this.session = data;
        if (this.session == null) {
          console.log('user must login')
        } else {
          this.$router.push({name: "collection"})
        }
      })
    }
  }
};
</script>

<style scoped>
</style>
