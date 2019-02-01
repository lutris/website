import timeago from 'timeago.js';
import axios from 'axios';
import Vue from 'vue';
import VueMaterial from 'vue-material';
import './assets/material.css';

import InstallerIssues from './components/InstallerIssues';

Vue.config.productionTip = false;
Vue.use(VueMaterial);

function formatTimeAgo(date) {
  if (!date) {
    return '';
  }
  return timeago().format(new Date(date));
}
Vue.filter('formatTimeAgo', formatTimeAgo);

if (process.env.NODE_ENV === 'development') {
  axios.defaults.baseURL = 'http://localhost:8000';
} else {
  axios.defaults.baseURL = 'https://lutris.net';
}

/* eslint-disable no-new */
new Vue({
  el: '#issues',
  components: { InstallerIssues },
});
