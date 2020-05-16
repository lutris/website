'use strict'
const webpack = require("webpack");
// const jquery = require('jquery');
const autoprefixer = require('autoprefixer');
const path = require('path');
const CopyPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
    entry: [
            // "jquery",
            "./frontend/js/app.js",
            "./frontend/css/lutris.scss",
        ],
    output: {
        path: path.resolve(__dirname, 'public'),
        filename: "js/app.js",
        // path to build relative asset links
        publicPath: "../"
    },
    devtool: "inline-source-map",
    mode: "development",
    module: {
        rules: [
            // {
            //     test: require.resolve('jquery'),
            //     use: [{
            //       loader: 'expose-loader',
            //       options: 'jQuery'
            //     },{
            //       loader: 'expose-loader',
            //       options: '$'
            //     }]
            // },
            // styles loader
            {
                test: /\.(sa|sc|c)ss$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    "css-loader",
                    "sass-loader"
                ],
            },

            // fonts loader
            {
                test: /\.(woff|woff2|eot|ttf|otf)$/,
                use: [
                    {
                        loader: "file-loader",
                        options: {
                            name: "fonts/[name].[ext]"
                        }
                    },
                ],
            },
        ]
    },
    plugins: [
        // save compiled SCSS into separated CSS file
        new MiniCssExtractPlugin({
            filename: "css/lutris.css"
        }),
        // provide jQuery and Popper.js dependencies
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            jquery: 'jquery',
            'window.jQuery': 'jquery',
            Popper: ['popper.js', 'default']
        }),
        // new CopyPlugin({
        //     patterns: [
        //         { from: path.resolve(__dirname, 'node_modules/ace-builds/src-noconflict/*'),
        //             to: path.resolve(__dirname, 'public/ace'),
        //             flatten: true },
        //         { from: path.resolve(__dirname, 'node_modules/ace-builds/src-noconflict/snippets/*'),
        //             to: path.resolve(__dirname, 'public/ace/snippets'),
        //             flatten: true },
        //     ]
        // }),
    ],
    // watch: true,
    // watchOptions: {
    //     ignored: /node_modules/,
    //     aggregateTimeout: 300,
    //     poll: 500
    //   },
};