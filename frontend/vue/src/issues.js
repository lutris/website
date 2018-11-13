import timeago from 'timeago.js';
import axios from 'axios';
import Vue from 'vue';
import 'vue-material/dist/vue-material.min.css';
import { MdDialogConfirm, MdButton } from 'vue-material/dist/components';
import { MdDialogContent } from 'vue-material/dist/components/MdDialog';
import InstallerIssues from './components/InstallerIssues';

Vue.config.productionTip = false;
Vue.use(MdDialogConfirm);
Vue.use(MdDialogContent);
Vue.use(MdButton);

function formatTimeAgo(date) {
  if (!date) {
    return '';
  }
  return timeago().format(new Date(date));
}
Vue.filter('formatTimeAgo', formatTimeAgo);

axios.defaults.baseURL = 'http://localhost:8000';

/* eslint-disable no-new */
new Vue({
  el: '#issues',
  components: { InstallerIssues },
  template: '<InstallerIssues slug="league-of-legends"/>',
});
