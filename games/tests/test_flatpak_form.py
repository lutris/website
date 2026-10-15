"""Integration tests for Flatpak installer form validation."""

from django.test import TestCase

from games.forms import InstallerForm
from runners.models import Runner

from . import factories


class FlatpakInstallerFormTests(TestCase):
    def setUp(self):
        self.game = factories.GameFactory(name="Flatpak Form Test")
        self.runner = Runner.objects.get(slug="flatpak")

    def make_form(self, script):
        return InstallerForm(
            data={
                "runner": str(self.runner.pk),
                "version": "Flatpak test",
                "description": "",
                "notes": "",
                "credits": "",
                "content": script,
            },
            instance=factories.InstallerDraftFactory.build(game=self.game),
        )

    def test_flathub_appid_is_accepted(self):
        form = self.make_form("game:\\n  appid: org.example.Game\\n".replace("\\n", "\n"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_appid_is_rejected(self):
        form = self.make_form("game:\\n  args: --fullscreen\\n".replace("\\n", "\n"))
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    def test_unknown_bundle_file_is_rejected(self):
        script = (
            "game:\n  appid: org.example.Game\n"
            "installer:\n  - task:\n      name: install_flatpak\n      file: missing\n"
        )
        form = self.make_form(script)
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    def test_valid_flatpak_form_can_be_saved_as_draft(self):
        form = self.make_form("game:\\n  appid: org.example.Game\\n".replace("\\n", "\n"))
        self.assertTrue(form.is_valid(), form.errors)
        draft = form.save()
        self.assertEqual(draft.runner.slug, "flatpak")
        self.assertEqual(draft.game, self.game)
        self.assertIn("org.example.Game", draft.content)
        self.assertTrue(draft.draft)
