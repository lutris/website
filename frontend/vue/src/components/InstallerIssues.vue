<template>
  <div>
    <h3>
      Issues for {{ slug }}
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
    <div v-for="installer in issues" v-bind:key="installer.slug">
      <div v-for="issue in installer.issues" v-bind:key="issue.id">
        <template v-if="!issue.solved || !hideResolvedIssues">
          <div class="issue" v-bind:class="{ solved: issue.solved }">
            <strong>{{ issue.username }}</strong>
            <em>{{ issue.submitted_on | formatDate }}</em>
            <p>{{ issue.description }}</p>
            <div v-if="issue.replies.length">
              <a href="#" v-bind:issue-id="issue.id" @click="onShowReplies">
                show {{ issue.replies.length }}
                {{ issue.replies.length > 1 ? 'replies' : 'reply' }}
              </a>
            </div>
            <transition name="slide-fade">
              <template v-if="displayedReplies == issue.id">
                <div class="installer-replies">
                  <div
                    v-for="reply in issue.replies"
                    v-bind:key="reply.submitted_on"
                  >
                    <div class="reply">
                      <strong>{{ reply.username }}</strong>
                      <em>{{ reply.submitted_on | formatDate }}</em>
                      <p>{{ reply.description }}</p>
                    </div>
                  </div>
                </div>
              </template>
            </transition>
          </div>
        </template>
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
      issues: [],
      displayedReplies: 0,
      hideResolvedIssues: true,
    };
  },
  mounted() {
    axios.get(`/api/installers/${this.slug}/issues`).then(response => {
      if (!response.data.count) {
        return;
      }
      this.issues = response.data.results;
    });
  },
  methods: {
    onShowReplies(event) {
      const issueId = parseInt(event.target.attributes['issue-id'].value, 10);
      const label = event.target.innerText;
      if (this.displayedReplies === issueId) {
        this.displayedReplies = 0;
        event.target.innerHTML = label.replace('hide', 'show');
      } else {
        this.displayedReplies = issueId;
        event.target.innerHTML = label.replace('show', 'hide');
      }
      event.preventDefault();
      return false;
    },
    onToggleResolvedIssues() {
      this.hideResolvedIssues = !this.hideResolvedIssues;
    },
  },
};
</script>

<style scoped>
.issue {
  padding: 0.5em;
  margin-bottom: 1.6em;
}
.solved {
  outline: 1px solid green;
}
.reply {
  margin-left: 1em;
}
strong {
  color: #e5ddd0;
}
a {
  font-size: 0.9em;
}
p {
  background-color: #3b3b3b;
  margin: 0;
  padding: 0.5em;
}
em {
  font-size: 0.8em;
}
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

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.5s ease;
}

.slide-fade-enter,
.slide-fade-leave-to {
  transform: translateY(30px);
  opacity: 0;
}
</style>
