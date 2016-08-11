from games import models


def get_unpublished_installers(count=10):
    return models.Installer.objects.filter(published=False).order_by('?')[:count]


def get_unpublished_screenshots(count=10):
    return models.Screenshot.objects.filter(published=False).order_by('?')[:count]


def get_unreviewed_game_submissions(count=10):
    return models.GameSubmission.objects.filter(accepted_at__isnull=True).order_by('?')[:count]


def get_installer_issues(count=10):
    return models.InstallerIssue.objects.all().order_by('?')[:count]


def get_mod_mail_content():
    return {
        'installers': get_unpublished_installers(),
        'screenshots': get_unpublished_screenshots(),
        'submissions': get_unreviewed_game_submissions(),
        'issues': get_installer_issues()
    }
