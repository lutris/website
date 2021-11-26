const { merge } = require('webpack-merge');
const common = require('./webpack.common.conf.js');

module.exports = merge(common, {
  mode: 'development',
  devtool: 'inline-source-map',
  devServer: {
    static: './public',
  },
});