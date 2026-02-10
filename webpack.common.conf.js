"use strict";
const webpack = require("webpack");
const path = require("path");
const CopyPlugin = require("copy-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
  entry: {
    lutris: "./frontend/js/app.js",
    editor: "./frontend/js/editor.js",
    styles: "./frontend/css/lutris.scss"
  },
  output: {
    path: path.resolve(__dirname, "public"),
    filename: "js/[name].js",
    // path to build relative asset links
    publicPath: "../",
  },
  module: {
    rules: [
      {
        test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        include: path.resolve(__dirname, './node_modules/bootstrap-icons/font/fonts'),
        use: {
            loader: 'file-loader',
            options: {
                name: '[name].[ext]',
                outputPath: 'webfonts',
                publicPath: '../webfonts',
            },
        }
      },
      // expose jQuery to other scripts
      {
        test: require.resolve("jquery"),
        use: [
          {
            loader: "expose-loader",
            options: {
              exposes: ["$", "jQuery"]
            }
          }
        ],
      },
      {
        test: /\.(jpg|png|svg|bmp|gif)$/,
        use: {
          loader: "url-loader",
        },
      },
      // styles loader
      {
        test: /\.(sa|sc|c)ss$/,
        use: [MiniCssExtractPlugin.loader, "css-loader", "sass-loader"],
      },
      // fonts loader
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/,
        use: [
          {
            loader: "file-loader",
            options: {
              name: "fonts/[name].[ext]",
            },
          },
        ],
      },
    ],
  },
  plugins: [
    // save compiled SCSS into separated CSS file
    new MiniCssExtractPlugin({
      filename: "css/[name].css",
    }),
    new CopyPlugin({
      patterns: [
        {
          from: path.resolve(__dirname, "node_modules/bootstrap-icons/font"),
          to: "./css/"
        },
        {
          from: path.resolve(__dirname, "node_modules/blueimp-gallery/css"),
          to: "./css/"
        },
        {
          from: path.resolve(__dirname, "node_modules/blueimp-gallery/js"),
          to: "./js/"
        },
        {
          from: path.resolve(__dirname, "node_modules/blueimp-gallery/img"),
          to: "./img/"
        },
        {
          from: path.resolve(__dirname, "node_modules/croppie/*.js"),
          to: "./js/[name][ext]"
        },
        {
          from: path.resolve(__dirname, "node_modules/croppie/*.css"),
          to: "./css/[name][ext]"
        },
      ],
    }),
    // provide jQuery and Popper.js dependencies
    new webpack.ProvidePlugin({
      $: "jquery",
      jquery: "jquery",
      "window.jQuery": "jquery",
      "window.$": "jquery",
      Popper: "@popperjs/core"
    }),
  ]
};
