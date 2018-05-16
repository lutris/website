from django.conf import settings
from games import models
from emails.messages import send_email

DEFAULT_COUNT = 12


def get_unpublished_installers(count=DEFAULT_COUNT):
    return models.Installer.objects.filter(published=False).order_by('?')[:count]


def get_unpublished_screenshots(count=DEFAULT_COUNT):
    return models.Screenshot.objects.filter(published=False).order_by('?')[:count]


def get_unreviewed_game_submissions(count=DEFAULT_COUNT):
    return models.GameSubmission.objects.filter(
        accepted_at__isnull=True
    ).order_by('?')[:count]


def get_installer_issues(count=DEFAULT_COUNT):
    return models.InstallerIssue.objects.all().order_by('?')[:count]


def get_mod_mail_content():
    return {
        'installers': get_unpublished_installers(),
        'screenshots': get_unpublished_screenshots(),
        'submissions': get_unreviewed_game_submissions(),
        'issues': get_installer_issues()
    }


def send_daily_mod_mail():
    from accounts.models import User
    context = get_mod_mail_content()
    if settings.DEBUG:
        moderators = [u[1] for u in settings.MANAGERS]
    else:
        moderators = [u.email for u in User.objects.filter(is_staff=True)]
    subject = 'Your daily moderator mail'
    return send_email('daily_mod_mail', context, subject, moderators)
