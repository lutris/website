<template>
  <section v-if="hasIssues">
    <div>
      <h3>
        Issues
        <span class="title-action">
          <input
            type="checkbox"
            id="resolved-issues-toggle"
            v-model="hideResolvedIssues"
            @click="onToggleResolvedIssues"
          />
          <label for="resolved-issues-toggle">Hide resolved issues</label>
        </span>
      </h3>
      <div v-for="installer in installer_issues" v-bind:key="installer.slug">
        <div v-for="(issue, index) in installer.issues" v-bind:key="issue.id">
          <template v-if="!issue.solved || !hideResolvedIssues">
            <installer-issue
              :issue="issue"
              :user="user"
              :installer_slug="installer.slug"
              :game_slug="slug"
              v-on:delete-issue="deleteIssue(installer.slug, index);"
            ></installer-issue>
          </template>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import axios from 'axios';
import InstallerIssue from './InstallerIssue';

export default {
  name: 'InstallerIssues',
  props: {
    slug: String,
  },
  data() {
    return {
      installer_issues: [],
      user: null,
      hideResolvedIssues: false,
    };
  },
  computed: {
    hasIssues() {
      for (let i = 0; i < this.installer_issues.length; i += 1) {
        const installer = this.installer_issues[i];
        if (installer.issues.length) {
          return true;
        }
      }
      return false;
    },
  },
  mounted() {
    axios.get(`/api/installers/${this.slug}/issues`).then(response => {
      if (!response.data.count) {
        return;
      }
      this.installer_issues = response.data.results;
    });

    axios.get('/api/users/me').then(response => {
      if (response.data) {
        this.user = response.data;
      } else {
        this.user = null;
      }
    });
  },
  methods: {
    onToggleResolvedIssues() {
      this.hideResolvedIssues = !this.hideResolvedIssues;
    },
    deleteIssue(installerSlug, index) {
      for (let i = 0; i < this.installer_issues.length; i += 1) {
        const installer = this.installer_issues[i];
        if (installer.slug === installerSlug) {
          installer.issues.splice(index, 1);
        }
      }
    },
  },
  components: {
    InstallerIssue,
  },
};
</script>

<style scoped>
.title-action {
  font-size: 0.7em;
  float: right;
  background-color: #3e3e3e;
  padding: 1px 12px;
  border-radius: 16px;
  line-height: 16px;
}
.title-action input {
  position: relative;
  top: -1px;
  vertical-align: middle;
}
.title-action label {
  font-weight: normal;
  color: #9b9b9b;
  vertical-align: middle;
  position: relative;
  top: 3px;
}
</style>
