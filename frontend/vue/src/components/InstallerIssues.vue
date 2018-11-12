<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <span>Issues</span>
  </div>
</template>

<script>
export default {
  name: 'InstallerIssues',
  data() {
    return {
      msg: 'Welcome to Your Vue.js App',
    };
  },
};
</script>

<style scoped>
h1,
h2 {
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
