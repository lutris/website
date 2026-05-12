"""One-shot notification to social-signup users that they can now set a password.

Users created via Discord/Google/Steam social login have an unusable password,
which means they cannot sign in to the Lutris desktop client (it only supports
username + password). This command emails them about the new self-service flow
at /accounts/password/set. Steam-only users have no email captured and are
skipped — they need to be reached via Discord/forum announcements instead.

Idempotent: each user's password_setup_notified_at is stamped after a
successful send, and already-stamped users are filtered out of subsequent runs.
"""

import time
from argparse import ArgumentParser

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from emails.messages import send_email


class Command(BaseCommand):
    help = __doc__.splitlines()[0]

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List target users without sending any email or updating records.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Cap the number of emails sent in this run.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.2,
            help="Seconds to sleep between sends to avoid SMTP throttling.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]
        sleep_seconds = options["sleep"]

        users = (
            User.objects.filter(
                socialaccount__isnull=False,
                password__startswith="!",
                password_setup_notified_at__isnull=True,
                is_active=True,
            )
            .exclude(email="")
            .distinct()
            .order_by("id")
        )
        if limit:
            users = users[:limit]

        total = users.count()
        self.stdout.write(f"Eligible users to notify: {total}")
        if dry_run:
            for user in users:
                joined = user.date_joined.date().isoformat() if user.date_joined else "?"
                self.stdout.write(
                    f"  would notify id={user.id} joined={joined} "
                    f"username={user.username} email={user.email}"
                )
            return

        set_password_url = "https://lutris.net" + reverse("password_set")
        sent = 0
        skipped = 0
        for user in users.iterator():
            provider = _primary_provider(user)
            context = {
                "username": user.username,
                "provider": provider,
                "set_password_url": set_password_url,
            }
            subject = "You can now set a password for your Lutris account"
            try:
                send_email("set_password_notification", context, subject, user.email)
            except Exception as exc:
                self.stderr.write(f"Failed to email user id={user.id}: {exc}")
                skipped += 1
                continue
            user.password_setup_notified_at = timezone.now()
            user.save(update_fields=["password_setup_notified_at"])
            sent += 1
            if sleep_seconds:
                time.sleep(sleep_seconds)

        self.stdout.write(
            self.style.SUCCESS(
                f"Sent: {sent}  Skipped: {skipped}  Send-emails setting: {settings.SEND_EMAILS}"
            )
        )


def _primary_provider(user) -> str:
    """Human-readable provider name for the email body."""
    account = SocialAccount.objects.filter(user=user).order_by("date_joined").first()
    if not account:
        return "a social login provider"
    return {
        "discord": "Discord",
        "google": "Google",
        "steam": "Steam",
    }.get(account.provider, account.provider.title())
