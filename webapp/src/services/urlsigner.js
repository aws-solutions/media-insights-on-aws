export default {
  getSignedURL(file, config) {
    return new Promise((resolve, reject) => {
      // var fd = new FormData();
      const token = config.token
      let request = new XMLHttpRequest(),
          signingURL = (typeof config.signingURL === "function") ?  config.signingURL(file) : config.signingURL;
      // console.log('signing URL: ', signingURL)
      request.open("POST", signingURL);
      request.setRequestHeader("Content-Type", "application/json");
      request.setRequestHeader("Authorization", token);
      // console.log(token)
      request.onload = function () {
        if (request.status == 200) {
          resolve(JSON.parse(request.response));
        } else {
          reject((request.statusText));
        }
      };
      request.onerror = function (err) {
        console.error("Network Error : Could not send request to AWS (Maybe CORS errors)");
        reject(err)
      };
      if (config.withCredentials === true) {
        request.withCredentials = true;
      }
      request.send("{\"S3Bucket\":\""+process.env.VUE_APP_DATAPLANE_BUCKET+"\",\"S3Key\":\""+file.name+"\"}");
    });
  },
  sendFile(file, config) {
    return this.getSignedURL(file, config)
      .then((response) => {return ({'success': true, 'message': response})});
  },
}
