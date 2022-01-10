"""Discord Webhook handlers"""
import json
import logging
import requests

from django.conf import settings

LOGGER = logging.getLogger(__name__)


def send_webhook_payload(hook_url, payload):
    """Send a payload to a Discord webhook"""
    hook_response = requests.post(hook_url, json.dumps(payload), headers={
        "Content-Type": "application/json"
    })
    if hook_response.status_code >= 400:
        LOGGER.error(
            "Discord responded with status %s while sending payload %s. Response text: %s",
            hook_response.status_code,
            payload,
            hook_response.text
        )
        return False
    return True


def notify_issue_reply(issue, user, description):
    """Notify of an issue reply"""
    title = (
        f"[reply] by {issue.submitted_by} for {issue.installer.version} on {issue.installer.game}"
    )
    notify_issue(issue, user, title, description)


def notify_issue_creation(issue, user, description):
    """Notify of an issue creation"""
    title = (
        f"[new] by {issue.submitted_by} for {issue.installer.version} on {issue.installer.game}"
    )
    notify_issue(issue, user, title, description)


def notify_issue(issue, user, title, description):
    """Sends an issue notification to Discord throught a Webhook"""
    if not settings.DISCORD_ISSUE_WEBHOOK_TOKEN:
        return
    hook_url = (
        f"https://discordapp.com/api/webhooks/"
        f"{settings.DISCORD_ISSUE_WEBHOOK_ID}/{settings.DISCORD_ISSUE_WEBHOOK_TOKEN}"
    )
    payload = {
        "embeds": [{
            "title": title,
            "description": description,
            "url": f"https://lutris.net/games/{issue.installer.game.slug}",
            "color": 13965399,
            "thumbnail": {
                "url": issue.installer.game.banner_url
            },
            "author": {
                "name": user.username,
                "url": f"https://lutris.net/admin/accounts/user/{user.id}/change"
            },
            "fields": []
        }]
    }
    return send_webhook_payload(hook_url, payload)


def notify_installer(installer):
    """Sends a notification to Discord through a Webhook"""
    if not settings.DISCORD_INSTALLER_WEBHOOK_TOKEN:
        return
    hook_url = (
        "https://discordapp.com/api/webhooks/"
        f"{settings.DISCORD_INSTALLER_WEBHOOK_ID}/{settings.DISCORD_INSTALLER_WEBHOOK_TOKEN}"
    )
    payload = {
        "embeds": [{
            "title": f"Installer created: {installer}" % installer,
            "description": f"Installer {installer.version} for {installer.runner}",
            "url": f"https://lutris.net/games/{installer.game.slug}",
            "color": 13965399,
            "thumbnail": {
                "url": installer.game.banner_url
            },
            "author": {
                "name": installer.user.username,
                "url": f"https://lutris.net/admin/accounts/user/{installer.user.id}/change"
            },
            "fields": []
        }]
    }
    return send_webhook_payload(hook_url, payload)
