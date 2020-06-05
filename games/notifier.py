"""Send a digest of unpublished content to moderators"""
from django.conf import settings
from accounts.models import User
from games import models
from emails.messages import send_email

DEFAULT_COUNT = 12


def get_unpublished_installers(count=DEFAULT_COUNT):
    """Return a random list of unpublished installers"""
    return models.Installer.objects.filter(
        published=False
    ).order_by('?')[:count]


def get_unpublished_screenshots(count=DEFAULT_COUNT):
    """Return a random list of unpublished screenshots"""
    return models.Screenshot.objects.filter(
        published=False
    ).order_by('?')[:count]


def get_unreviewed_game_submissions(count=DEFAULT_COUNT):
    """Return a random list of unreviewed game submissions"""
    return models.GameSubmission.objects.filter(
        accepted_at__isnull=True
    ).order_by('?')[:count]


def get_installer_issues(count=DEFAULT_COUNT):
    """Return a random list of installer issues"""
    return models.InstallerIssue.objects.all().order_by('?')[:count]


def get_mod_mail_content():
    """Get the payload to be included in the digest"""
    return {
        'installers': get_unpublished_installers(),
        'screenshots': get_unpublished_screenshots(),
        'submissions': get_unreviewed_game_submissions(),
        'issues': get_installer_issues()
    }


def send_daily_mod_mail():
    """Send the email to moderators"""
    context = get_mod_mail_content()
    if settings.DEBUG:
        moderators = [u[1] for u in settings.MANAGERS]
    else:
        moderators = [u.email for u in User.objects.filter(is_staff=True)]
    subject = 'Your daily moderator mail'
    return send_email('daily_mod_mail', context, subject, moderators)
