"""Authenticated HTTP tests for the Flatpak installer submission lifecycle."""

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from games import models

from . import factories

YUNO_SCRIPT = """files:
- engine: https://github.com/nunuhara/ai5-sdl2/releases/download/1.5.0/ai5-sdl2-linux-x86_64-1.5.0.flatpak
- font:
     url: https://github.com/xerysherry/uEmuera/raw/refs/heads/master/Assets/Resources/Fonts/MS%20PGothic.ttf
     filename: MS PGothic.ttf
- data: https://archive.org/download/yuno.-7z/YUNO.7z
game:
  appid: technology.haniwa.ai5-sdl2
  args: '--font "MS PGothic.ttf"'
installer:
- task:
     name: install_flatpak
     file: engine
- extract:
     file: data
     dst: $GAMEDIR
- copy:
     src: font
     dst: $GAMEDIR
"""


class FlatpakSubmissionHTTPTests(TestCase):
    def setUp(self):
        self.game = factories.GameFactory(name="YUNO HTTP Test")
        self.submitter = factories.UserNoLibraryFactory()
        self.moderator = factories.UserNoLibraryFactory(is_staff=True, is_superuser=True)
        self.client = APIClient()
        self.list_url = reverse("api_installer_draft_list")

    def submit_yuno(self, draft=False):
        self.client.force_authenticate(user=self.submitter)
        return self.client.post(
            self.list_url,
            {
                "game_slug": self.game.slug,
                "runner": "flatpak",
                "version": "YUNO Flatpak",
                "content": YUNO_SCRIPT,
                "draft": draft,
            },
            format="json",
        )

    def test_anonymous_submission_requires_authentication(self):
        response = self.client.post(
            self.list_url,
            {
                "game_slug": self.game.slug,
                "runner": "flatpak",
                "version": "YUNO Flatpak",
                "content": YUNO_SCRIPT,
            },
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(models.InstallerDraft.objects.count(), 0)

    def test_authenticated_submission_enters_moderation_queue(self):
        response = self.submit_yuno()
        self.assertEqual(response.status_code, 201, response.data)
        submission = models.InstallerDraft.objects.get(game=self.game)
        self.assertEqual(submission.user, self.submitter)
        self.assertEqual(submission.runner.slug, "flatpak")
        self.assertFalse(submission.draft)
        self.assertIn("technology.haniwa.ai5-sdl2", submission.content)

        self.client.force_authenticate(user=self.moderator)
        queue = self.client.get(self.list_url, {"type": "submission"})
        self.assertEqual(queue.status_code, 200)
        self.assertTrue(any(item["id"] == submission.pk for item in queue.data["results"]))

    def test_moderator_accepts_yuno_submission(self):
        response = self.submit_yuno()
        self.assertEqual(response.status_code, 201, response.data)
        submission = models.InstallerDraft.objects.get(game=self.game)

        self.client.force_authenticate(user=self.moderator)
        response = self.client.post(
            reverse("api_installer_draft_accept", kwargs={"pk": submission.pk}),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(models.InstallerDraft.objects.filter(pk=submission.pk).exists())
        installer = models.Installer.objects.get(game=self.game, version="YUNO Flatpak")
        self.assertEqual(installer.runner.slug, "flatpak")
        self.assertTrue(installer.published)
        self.assertIn("install_flatpak", installer.content)

    def test_unsubmitted_draft_cannot_be_accepted(self):
        response = self.submit_yuno(draft=True)
        self.assertEqual(response.status_code, 201, response.data)
        submission = models.InstallerDraft.objects.get(game=self.game)
        self.client.force_authenticate(user=self.moderator)
        response = self.client.post(
            reverse("api_installer_draft_accept", kwargs={"pk": submission.pk}),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(models.InstallerDraft.objects.filter(pk=submission.pk).exists())

    @patch("games.models.notify_rejected_installer")
    def test_moderator_rejects_yuno_submission(self, notify):
        response = self.submit_yuno()
        self.assertEqual(response.status_code, 201, response.data)
        submission = models.InstallerDraft.objects.get(game=self.game)
        self.client.force_authenticate(user=self.moderator)
        response = self.client.post(
            reverse("api_installer_draft_reject", kwargs={"pk": submission.pk}),
            {"review": "Please review the bundle source."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        submission.refresh_from_db()
        self.assertTrue(submission.draft)
        self.assertEqual(submission.review, "Please review the bundle source.")
        notify.assert_called_once()

    def test_published_yuno_is_exposed_to_lutris_client(self):
        """The public game installer API must expose the runner and parsed script."""
        response = self.submit_yuno()
        self.assertEqual(response.status_code, 201, response.data)
        submission = models.InstallerDraft.objects.get(game=self.game)

        self.client.force_authenticate(user=self.moderator)
        accepted = self.client.post(
            reverse("api_installer_draft_accept", kwargs={"pk": submission.pk}),
            {},
            format="json",
        )
        self.assertEqual(accepted.status_code, 200, accepted.data)

        self.client.force_authenticate(user=None)
        response = self.client.get(
            reverse("api_game_installer_list", kwargs={"slug": self.game.slug})
        )
        self.assertEqual(response.status_code, 200)
        installers = response.data["results"]
        yuno = next(item for item in installers if item["version"] == "YUNO Flatpak")
        self.assertEqual(yuno["runner"], "flatpak")
        self.assertEqual(yuno["game_slug"], self.game.slug)
        self.assertEqual(yuno["script"]["game"]["appid"], "technology.haniwa.ai5-sdl2")
        self.assertEqual(
            [step.get("task", {}).get("name") for step in yuno["script"]["installer"]],
            ["install_flatpak", None, None],
        )
        self.assertEqual(yuno["script"]["installer"][0]["task"]["file"], "engine")
