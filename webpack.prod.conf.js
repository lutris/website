const { merge } = require('webpack-merge');
const path = require("path");
const common = require('./webpack.common.conf.js');

module.exports = merge(common, {
  mode: 'production',
  output: {
    path: path.resolve(__dirname, "public"),
    filename: "js/app.min.js",
    // path to build relative asset links
    publicPath: "../",
  },
});