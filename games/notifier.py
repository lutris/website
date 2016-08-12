from games import models

DEFAULT_COUNT = 12


def get_unpublished_installers(count=DEFAULT_COUNT):
    return models.Installer.objects.filter(published=False).order_by('?')[:count]


def get_unpublished_screenshots(count=DEFAULT_COUNT):
    return models.Screenshot.objects.filter(published=False).order_by('?')[:count]


def get_unreviewed_game_submissions(count=DEFAULT_COUNT):
    return models.GameSubmission.objects.filter(accepted_at__isnull=True).order_by('?')[:count]


def get_installer_issues(count=DEFAULT_COUNT):
    return models.InstallerIssue.objects.all().order_by('?')[:count]


def get_mod_mail_content():
    return {
        'installers': get_unpublished_installers(),
        'screenshots': get_unpublished_screenshots(),
        'submissions': get_unreviewed_game_submissions(),
        'issues': get_installer_issues()
    }
