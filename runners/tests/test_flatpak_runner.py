"""Tests for Flatpak runner registration and installer form availability."""

from django.test import TestCase

from games.forms import InstallerForm
from runners.models import Runner


class FlatpakRunnerTests(TestCase):
    def test_flatpak_runner_registered_by_migration(self):
        runner = Runner.objects.get(slug="flatpak")
        self.assertEqual(runner.name, "Flatpak")
        self.assertEqual(runner.website, "https://flatpak.org")

    def test_flatpak_runner_available_in_installer_form(self):
        runner = Runner.objects.get(slug="flatpak")
        form = InstallerForm()
        self.assertTrue(form.fields["runner"].queryset.filter(pk=runner.pk).exists())
