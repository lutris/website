import timeago from 'timeago.js';
import Vue from 'vue';
import InstallerIssues from './components/InstallerIssues';

Vue.config.productionTip = false;

function formatDate(date) {
  if (!date) {
    return '';
  }
  return timeago().format(new Date(date));
}

Vue.filter('formatDate', formatDate);
/* eslint-disable no-new */
new Vue({
  el: '#installer-issues',
  components: { InstallerIssues },
});
