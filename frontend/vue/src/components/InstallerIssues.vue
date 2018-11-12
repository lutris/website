<template>
  <div>
    <h3>Issues</h3>
    <ul v-for="issue in issues">
      <li>{{ issue }}</li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'InstallerIssues',
  data() {
    return {
      issues: ['ahh', 'ohh nooo', 'bli  blu'],
      msg: 'Here are installer issues',
    };
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
  color: #42b983;
}
</style>
