<template>
  <div>
    <amplify-authenticator></amplify-authenticator>
  </div>
</template>

<script>
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
