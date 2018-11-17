"""Discord Webhook handlers"""
import json
import logging
import requests

from django.conf import settings

LOGGER = logging.getLogger(__name__)


def notify_issue_reply(issue, user, description):
    """Notify of an issue reply"""
    title = "Reply to issue by {} for {}".format(
        issue.submitted_by,
        issue.installer.version
    )
    notify_issue(issue, user, title, description)


def notify_issue_creation(issue, user, description):
    """Notify of an issue creation"""
    title = "Issue submitted by {} for {}".format(
        issue.submitted_by,
        issue.installer.version
    )
    notify_issue(issue, user, title, description)


def notify_issue(issue, user, title, description):
    """Sends a notification to Discord throught a Webhook"""
    if not settings.DISCORD_ISSUE_WEBHOOK_TOKEN:
        return
    hook_url = "https://discordapp.com/api/webhooks/{}/{}".format(
        settings.DISCORD_ISSUE_WEBHOOK_ID,
        settings.DISCORD_ISSUE_WEBHOOK_TOKEN
    )
    payload = {
        "embeds": [{
            "title": title,
            "description": description,
            "url": "https://lutris.net/games/{}".format(
                issue.installer.game.slug
            ),
            "color": 13965399,
            "thumbnail": {
                "url": "https://lutris.net{}".format(issue.installer.game.banner_url)
            },
            "author": {
                "name": user.username,
                "url": "https://lutris.net/admin/accounts/user/{}/change/".format(
                    user.id
                )
            },
            "fields": []
        }]
    }
    hook_response = requests.post(hook_url, json.dumps(payload), headers={
        "Content-Type": "application/json"
    })
    LOGGER.info("Discord Webhook responded with status %s", hook_response.status_code)
    if hook_response.status_code >= 400:
        LOGGER.error("Error sending the hook payload: %s", hook_response.text)
        return False
    return True
