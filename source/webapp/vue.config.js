var SriPlugin = require('webpack-subresource-integrity');

module.exports = {
  configureWebpack: {
    output: {
      crossOriginLoading: 'anonymous',
    },
    plugins: [
      new SriPlugin({
        hashFuncNames: ['sha256', 'sha384'],
        enabled: false
      }),
    ],
    performance: {
      hints: false
    }
  }
};
