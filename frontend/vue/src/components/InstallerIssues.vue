<template>
  <div>
    <h3 class="issue">Issues for {{ slug }}</h3>
    <div v-for="installer in issues" v-bind:key="installer.slug">
      <div
        v-for="issue in installer.issues"
        v-bind:key="issue.id"
        class="issue"
      >
        <h4>Installer: {{ issue.installer }} by {{ issue.username }}</h4>
        <p>{{ issue.description }}</p>
        <div v-for="reply in issue.replies" v-bind:key="reply.submitted_on">
          <span>{{ reply.username }}</span>
          <p>{{ reply.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'InstallerIssues',
  props: {
    slug: String,
  },
  data() {
    return {
      issues: ['ahh', 'ohh nooo', 'bli  blu'],
      msg: 'Here are installer issues',
    };
  },
  mounted() {
    axios.get(`/api/installers/${this.slug}/issues`).then(response => {
      if (!response.data.count) {
        console.error("Can't load results");
        return;
      }
      this.issues = response.data.results;
      console.log(this.issues);
    });
  },
};
</script>

<style scoped>
h3 {
  font-weight: normal;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #666777;
}
</style>
