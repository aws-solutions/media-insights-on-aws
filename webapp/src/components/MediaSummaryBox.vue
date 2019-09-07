<template>
      <b-container fluid>
        <b-row align-v="center" class="my-1">
          <b-col>
            <label>Asset ID:</label>
            {{ this.$route.params.asset_id }}
            <br>
            <label>Source:</label>
            {{ s3_uri }}
            <br>
            <label>Filename:</label>
            {{ filename }}
          </b-col>
        </b-row>
        <br>
      </b-container>
</template>

<script>
export default {
  name: 'MediaSummary',
  props: ['s3_uri','filename'],
  data () {
    return {
    }
  }
}
</script>

<style>

</style>
