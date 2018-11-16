<template>
  <div class="issue" v-bind:class="{ solved: issue.solved }">
    <template v-if="issue.solved">
      <span class="solved-badge">Solved!</span>
    </template>
    <strong>{{ issue.username }}</strong> <strong>{{ installer_slug }}</strong>
    <em :title="getDate(issue.submitted_on)">
      {{ issue.submitted_on | formatTimeAgo }}
    </em>
    <p v-html="getMarkup(issue.description)"></p>
    <span v-if="issue.replies.length">
      <a href="#" @click.prevent="onShowReplies">
        show {{ issue.replies.length }}
        {{ issue.replies.length > 1 ? 'replies' : 'reply' }}
      </a>
    </span>
    <span> <a href="#" @click.prevent="onReplyClick">reply</a> </span>
    <span v-if="canSolveIssue">
      <a href="#" @click.prevent="onMarkAsSolved">mark as solved</a>
    </span>
    <span v-if="canDeleteIssue">
      <a href="#" @click.prevent="onDelete">delete</a>
    </span>

    <transition name="slide-fade">
      <template v-if="showReplyForm">
        <div class="issue-reply-form">
          <textarea v-model="replyContent"></textarea>
          <button :disabled="replyContent.length == 0" @click="onSubmitClick">
            Submit
          </button>
        </div>
      </template>
    </transition>

    <transition name="slide-fade">
      <template v-if="showReplies">
        <div class="installer-replies">
          <div v-for="reply in issue.replies" v-bind:key="reply.submitted_on">
            <div class="reply">
              <strong>{{ reply.username }}</strong>
              <em :title="getDate(reply.submitted_on)">
                {{ reply.submitted_on | formatTimeAgo }}
              </em>
              <span v-if="canDeleteReply(reply)">
                <a href="#" @click.prevent="onDeleteReply(reply);">delete</a>
              </span>
              <p v-html="getMarkup(reply.description)"></p>
            </div>
          </div>
        </div>
      </template>
    </transition>
    <md-dialog-confirm
      :md-active.sync="showSolvedConfirmation"
      md-title="Close this issue?"
      md-content="If this issue is solved, you can mark as closed. Make sure to indicate any solution you've used to help other users."
      md-confirm-text="Yes"
      md-cancel-text="No"
      @md-cancel="showSolvedConfirmation = false;"
      @md-confirm="onSolvedConfirmed"
      style="background-color: #444444;"
    />
    <md-dialog-confirm
      :md-active.sync="showDeleteConfirmation"
      md-title="Delete this issue?"
      md-content="This will complety erase the issue."
      md-confirm-text="Yes"
      md-cancel-text="No"
      @md-cancel="showDeleteConfirmation = false;"
      @md-confirm="onDeleteConfirmed"
      style="background-color: #444444;"
    />
    <md-dialog-confirm
      :md-active.sync="showDeleteReplyConfirmation"
      md-title="Delete this reply?"
      md-content="This will complety erase this reply."
      md-confirm-text="Yes"
      md-cancel-text="No"
      @md-cancel="showDeleteReplyConfirmation = false;"
      @md-confirm="onDeleteReplyConfirmed"
      style="background-color: #444444;"
    />
  </div>
</template>

<script>
import axios from 'axios';
import Cookies from 'js-cookie';
import anchorme from 'anchorme';

export default {
  name: 'InstallerIssue',
  props: {
    game_slug: String,
    user: Object,
    installer_slug: String,
    issue: Object,
  },
  data() {
    return {
      showReplies: false,
      showReplyForm: false,
      showSolvedConfirmation: false,
      showDeleteConfirmation: false,
      showDeleteReplyConfirmation: false,
      replyContent: '',
      deletedReplyId: null,
    };
  },
  computed: {
    canSolveIssue() {
      if (this.issue.solved || !this.user) {
        return false;
      }
      return this.user.is_staff || this.user.id === this.issue.submitted_by;
    },
    canDeleteIssue() {
      if (!this.user) {
        return false;
      }
      return this.user.is_staff || this.user.id === this.issue.submitted_by;
    },
  },
  methods: {
    canDeleteReply(reply) {
      if (!this.user) {
        return false;
      }
      return this.user.is_staff || this.user.id === reply.submitted_by;
    },
    getDate(date) {
      if (!date) {
        return '';
      }
      return new Date(date).toLocaleString();
    },
    getMarkup(text) {
      return anchorme(text);
    },
    onShowReplies(event) {
      const link = event.target;
      const label = event.target.innerText;
      if (this.showReplies) {
        this.showReplies = false;
        link.innerHTML = label.replace('hide', 'show');
      } else {
        this.showReplies = true;
        link.innerHTML = label.replace('show', 'hide');
      }
    },
    onReplyClick() {
      this.showReplyForm = !this.showReplyForm;
    },
    onSubmitClick() {
      const config = {
        headers: {
          'X-CSRFToken': Cookies.get('csrftoken'),
          'Content-Type': 'application/json',
        },
      };
      const payload = { description: this.replyContent };
      const url = `/api/installers/issues/${this.issue.id}`;
      axios.post(url, payload, config).then(response => {
        this.issue.replies.push(response.data);
        this.replyContent = '';
        this.showReplies = true;
        this.showReplyForm = false;
      });
    },
    onMarkAsSolved() {
      this.showSolvedConfirmation = true;
    },
    getAxiosConfig() {
      return {
        headers: {
          'X-CSRFToken': Cookies.get('csrftoken'),
          'Content-Type': 'application/json',
        },
      };
    },
    onSolvedConfirmed() {
      const url = `/api/installers/issues/${this.issue.id}`;
      axios
        .patch(url, { solved: true }, this.getAxiosConfig())
        .then(response => {
          if (!response.data.solved) {
            // The installer wasn't solved on the backend, the action failed
            return;
          }
          this.issue.solved = true;
          this.showSolvedConfirmation = false;
        });
    },
    onDelete() {
      this.showDeleteConfirmation = true;
    },
    onDeleteConfirmed() {
      const url = `api/installers/issues/${this.issue.id}`;
      axios.delete(url, this.getAxiosConfig()).then(response => {
        if (response.status === 204) {
          this.$emit('delete-issue');
        }
      });
    },
    onDeleteReply(reply) {
      this.deletedReplyId = reply.id;
      this.showDeleteReplyConfirmation = true;
    },
    onDeleteReplyConfirmed() {
      const url = `api/installers/issue-replies/${this.deletedReplyId}`;
      axios.delete(url, this.getAxiosConfig()).then(response => {
        if (response.status === 204) {
          this.$emit('delete-reply', this.deletedReplyId);
        }
      });
    },
  },
};
</script>

<style scoped>
.issue {
  padding: 0.5em;
  margin-bottom: 1.6em;
}
.reply {
  margin-left: 1em;
}
strong {
  color: #e5ddd0;
}
a {
  font-size: 0.9em;
  margin-right: 2em;
}
p {
  background-color: #3b3b3b;
  margin: 0;
  padding: 0.5em;
  white-space: pre-wrap;
}
em {
  font-size: 0.8em;
}

.issue-reply-form textarea {
  width: 100%;
  height: 175px;
  background-color: #5e5e5e;
  border: none;
  padding: 0.5em;
}
.issue-reply-form button {
  float: right;
  background-color: #bb6e20;
  border-radius: 6px;
  border: none;
  padding: 2px 12px;
  font-weight: bold;
}
.issue-reply-form button:disabled {
  background-color: #e3af7a;
}

.solved-badge {
  background-color: green;
  float: right;
  position: relative;
  border-radius: 2px;
  padding: 2px 6px;
  font-size: 0.8em;
  text-transform: uppercase;
}
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.5s ease;
}

.slide-fade-enter,
.slide-fade-leave-to {
  transform: translateY(-40px);
  opacity: 0;
}
</style>
