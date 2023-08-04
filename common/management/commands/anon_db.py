# pylint: disable=no-member
"""Remove any personally identifying information from the database"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django_openid_auth.models import UserOpenID
from rest_framework.authtoken.models import Token
from axes.models import AccessAttempt, AccessLog
from games.models import (
    Installer,
    InstallerDraft,
    InstallerIssue,
    InstallerIssueReply,
    InstallerHistory,
    Screenshot,
    GameSubmission,
)
from accounts.models import User
from common.models import Upload, News


class Command(BaseCommand):
    """Django command to anonymize the database"""

    @staticmethod
    def get_main_user():
        """Return the only user remaining in the DB"""
        return User.objects.first()

    @staticmethod
    def delete_tokens():
        """Remove all auth tokens (OpenID, DRF, ...)"""
        res = UserOpenID.objects.all().delete()
        print("Deleted %s openids" % res[0])

        res = Token.objects.all().delete()
        print("Deleted %s tokens" % res[0])

        res = LogEntry.objects.all().delete()
        print("Deleted %s log entries" % res[0])

        res = AccessLog.objects.all().delete()
        print("Deleted %s access log entries" % res[0])

        res = AccessAttempt.objects.all().delete()
        print("Deleted %s access attempt entries" % res[0])

    def handle(self, *args, **_kwargs):
        if not settings.DEBUG:
            raise RuntimeError("Never run this in production")

        self.delete_tokens()

        user = self.get_main_user()

        res = InstallerIssue.objects.all().update(submitted_by=user)
        print("Updated %s issues" % res)

        res = InstallerIssueReply.objects.all().update(submitted_by=user)
        print("Updated %s issue replies" % res)

        res = InstallerHistory.objects.all().update(user=user)
        print("Updated %s installer history" % res)

        res = Installer.objects.all().update(user=user)
        print("Updated %s installers" % res)

        res = InstallerHistory.objects.all().update(user=user)
        print("Updated %s installer history" % res)

        res = GameSubmission.objects.all().update(user=user)
        print("Updated %s game submissions" % res)

        res = Screenshot.objects.all().update(uploaded_by=user)
        print("Updated %s screenshots" % res)

        res = Upload.objects.all().update(uploaded_by=user)
        print("Updated %s uploads" % res)

        res = News.objects.all().update(user=user)
        print("Updated %s news" % res)

        res = InstallerDraft.objects.all().update(user=user)
        print("Updated %s drafts" % res)

        res = User.objects.exclude(pk=user.id).delete()
        print("Deleted %s users" % res[0])

        default_password = "lutris"
        user.set_password(default_password)
        user.username = "lutris"
        user.email = "root@localhost"
        user.website = ""
        user.steamid = ""
        user.save()
        print("Password for user %s is now %s" % (user, default_password))
