<template>
  <div class="issue" v-bind:class="{ solved: issue.solved }">
    <template v-if="issue.solved">
      <span class="solved-badge">Solved!</span>
    </template>
    <strong>{{ issue.username }}</strong>
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
    <span v-if="canReopenIssue">
      <a href="#" @click.prevent="onReopen">re-open</a>
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
    canReopenIssue() {
      if(!this.issue.solved || !this.user) {
        return false;
      }
      return this.user.is_staff || this.user.id === this.issue.submitted_by;
    }
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
    onReopen() {
      axios
        .patch(`/api/installers/issues/${this.issue.id}`, { solved: false }, this.getAxiosConfig())
        .then(response => {
          this.issue.solved = false;
        });
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
.md-dialog-title {
    margin-bottom: 20px;
    padding: 24px 24px 0;
}
.md-title {
    font-size: 20px;
    font-weight: 500;
    letter-spacing: .005em;
    line-height: 26px;
}
.md-dialog {
    box-shadow: 0 11px 15px -7px rgba(0,0,0,.2),0 24px 38px 3px rgba(0,0,0,.14),0 9px 46px 8px rgba(0,0,0,.12);
    min-width: 280px;
    max-width: 80%;
    max-height: 80%;
    margin: auto;
    display: flex;
    flex-flow: column;
    flex-direction: column;
    flex-direction: row;
    overflow: hidden;
    position: fixed;
    top: 50%;
    left: 50%;
    z-index: 11;
    border-radius: 2px;
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
    pointer-events: auto;
    transform: translate(-50%,-50%);
    transform-origin: center center;
    transition: opacity .15s cubic-bezier(.25,.8,.25,1),transform .2s cubic-bezier(.25,.8,.25,1);
    will-change: opacity,transform,left,top;
}
.md-dialog-container, .md-dialog-container .md-tabs {
    flex: 1;
}
.md-dialog-container {
    display: flex;
    flex-flow: column;
}
.md-dialog-content {
    padding: 0 24px 24px;
    flex: 1;
    flex-basis: 0%;
    flex-basis: auto;
    overflow: auto;
    position: relative;
}
.md-dialog-actions {
    min-height: 52px;
    padding: 8px 8px 8px 24px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    position: relative;
}
.md-button::before {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: 1;
    opacity: 0;
    transition: .4s cubic-bezier(.4,0,.2,1);
    will-change: background-color,opacity;
    content: " ";
}
.md-dialog-actions .md-button {
    min-width: 64px;
    margin: 0;
}
.md-button:not([disabled]) {
    cursor: pointer;
}
.md-button {
    min-width: 88px;
    height: 36px;
    margin: 6px 8px;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    user-select: none;
    border-radius: 2px;
    font-size: 14px;
    font-weight: 500;
    text-transform: uppercase;
}
.md-button, .md-button-clean {
    margin: 0;
    padding: 0;
    display: inline-block;
    position: relative;
    overflow: hidden;
    outline: none;
    background: transparent;
    border: 0;
    border-radius: 0;
    transition: .4s cubic-bezier(.4,0,.2,1);
    font-family: inherit;
    line-height: normal;
    text-decoration: none;
    vertical-align: top;
    white-space: nowrap;
}
.md-dialog-actions .md-button + .md-button {
    margin-left: 8px;
}
</style>
