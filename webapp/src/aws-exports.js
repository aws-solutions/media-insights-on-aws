const awsconfig = {
    Auth: {
      region: process.env.VUE_APP_AWS_REGION,
      userPoolId: process.env.VUE_APP_USER_POOL_ID,
      userPoolWebClientId: process.env.VUE_APP_USER_POOL_CLIENT_ID,
      identityPoolId: process.env.VUE_APP_IDENTITY_POOL_ID
    },
    API: {
      endpoints: [
        {
          name: "mieElasticsearch",
          endpoint: process.env.VUE_APP_ELASTICSEARCH_ENDPOINT,
          service: "es",
          region: process.env.VUE_APP_AWS_REGION
        }
      ]
    }
  };
  
  export default awsconfig;