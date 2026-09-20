"""Test cases for game API"""

import json
import logging
from unittest import skipUnless
from unittest.mock import MagicMock, patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import BannedAccount, User
from common.models import KeyValueStore
from games import antispam, models
from games.models import GameLibrary, SpamDomain
from providers.models import Provider, ProviderGame

from . import factories

LOGGER = logging.getLogger(__name__)


class TestGameApi(TestCase):
    """Test case for game API views"""

    def setUp(self):
        self.num_games = 10
        self.games = [
            factories.GameFactory(name="game_%d" % index, slug="game-%d" % index)
            for index in range(self.num_games)
        ]

    def test_can_get_games(self):
        """The API should return a list of games"""
        game_list_url = reverse("api_game_list")
        response = self.client.get(game_list_url)
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content.decode())
        self.assertEqual(len(games["results"]), self.num_games)

    def test_can_get_subset_of_games(self):
        """The API should filter by a given list of game slugs"""
        game_slugs = {"games": ["game-1", "game-2", "game-4"]}
        game_list_url = reverse("api_game_list")
        response = self.client.get(
            game_list_url, data=game_slugs, extra={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content.decode())
        self.assertEqual(len(games["results"]), len(game_slugs["games"]))

    def test_can_post_subset_of_games(self):
        """The API can use a POST request to query a list of games, allowing
        users to pass a longer list
        """
        game_slugs = {"games": ["game-1", "game-2", "game-4"]}
        game_list_url = reverse("api_game_list")
        response = self.client.post(
            game_list_url, data=json.dumps(game_slugs), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content.decode())
        self.assertEqual(len(games["results"]), len(game_slugs["games"]))

    def test_can_query_game_details(self):
        """The API can return details about a game"""
        response = self.client.get(reverse("api_game_detail", kwargs={"slug": "game-1"}))
        self.assertEqual(response.status_code, 200)


class TestGameLibraryApi(TestCase):
    """Test case for user library API views"""

    def setUp(self):
        game = factories.GameFactory
        games = [game() for i in range(5)]
        self.library = factories.GameLibraryFactory(games=games)
        other_games = [game(name="Metroid"), game(name="Mario")]
        self.other_library = factories.GameLibraryFactory(games=other_games)

    def test_anonymous_requests_are_rejected(self):
        """Anonymous users shouldn't be able to view a library"""
        user = self.library.user
        library_url = reverse("api_game_library", kwargs={"username": user.username})
        response = self.client.get(library_url)
        self.assertEqual(response.status_code, 401)

    def test_can_get_library(self):
        """Users should be logged in to access a library"""
        user = self.library.user
        self.client.login(username=user.username, password="password")
        library_url = reverse("api_game_library", kwargs={"username": user.username})
        response = self.client.get(library_url)
        self.assertEqual(response.status_code, 200)


class TestInstallerApi(TestCase):
    """Test case of installer API views"""

    def setUp(self):
        self.slug = "strider"
        self.game = factories.GameFactory(name=self.slug)
        factories.RunnerFactory(name="Linux", slug="linux")
        platform = factories.PlatformFactory()
        platform.default_installer = {"game": {"rom": "foo"}, "runner": "linux"}
        platform.save()  # pylint: disable=no-member
        self.game.platforms.add(platform)

    def test_can_get_installer_list_for_a_game(self):
        """The API can return a list of installers for a game"""
        self.assertTrue(self.game.platforms.count())
        response = self.client.get(reverse("api_game_installer_list", kwargs={"slug": self.slug}))
        self.assertEqual(response.status_code, 200)

    def test_get_installers_list_filtered(self):
        """The API returns a list of installers by filter"""
        self.assertTrue(self.game.platforms.count())
        inst_mgr = models.Installer.objects
        inst_mgr.get_filtered = MagicMock()
        period_start = "2020-01-01T00:00:00"
        period_end = "2021-01-01T00:00:00"
        response = self.client.get(
            reverse("api_installer_list"),
            {
                "status": "published",
                "revision": "final",
                "created_from": period_start,
                "created_to": period_end,
                "updated_from": period_start,
                "updated_to": period_end,
            },
        )
        inst_mgr.get_filtered.assert_called_with(
            {
                "published": True,
                "draft": False,
                "created_from": period_start,
                "created_to": period_end,
                "updated_from": period_start,
                "updated_to": period_end,
            }
        )
        self.assertEqual(response.status_code, 200)

    def test_get_installers_history_list_filtered(self):
        """The API returns a list of installers history by filter"""
        self.assertTrue(self.game.platforms.count())
        inst_mgr = models.InstallerHistory.objects
        inst_mgr.get_filtered = MagicMock()
        period_start = "2020-01-01T00:00:00"
        period_end = "2021-01-01T00:00:00"
        response = self.client.get(
            reverse("api_installer_history_list"),
            {
                "created_from": period_start,
                "created_to": period_end,
            },
        )
        inst_mgr.get_filtered.assert_called_with(
            {
                "created_from": period_start,
                "created_to": period_end,
            }
        )
        self.assertEqual(response.status_code, 200)

    def test_can_get_installer_history_for_installer(self):
        """The API can return a history for a given installer"""
        response = self.client.get(reverse("api_installer_history", kwargs={"installer_id": 1307}))
        self.assertEqual(response.status_code, 200)


class TestGameProviderApi(TestCase):
    """Test case for 3rd party game services integration"""

    def setUp(self):
        self.games = [
            factories.GameFactory(
                name="game_%d" % index, slug="game-%d" % index, gogid=str(1234 + index)
            )
            for index in range(10)
        ]
        provider = Provider.objects.create(name="gog", website="https://gogdb.org")
        for game in self.games:
            provider_game = ProviderGame.objects.create(
                name=game.name, slug=game.gogid, provider=provider
            )
            game.provider_games.add(provider_game)

    def test_can_get_games_by_gogid(self):
        """The game list API can be queried by GOG ID"""
        gogids = {"gogid": ["1234", "1235", "1236"]}
        response = self.client.post(
            reverse("api_game_list"), data=json.dumps(gogids), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        games = json.loads(response.content.decode())
        self.assertEqual(len(games["results"]), 3)

    def test_can_receive_garbage_in_gogids(self):
        """The view should not crash when passed invalid GOG IDs"""
        gogids = {"gogid": ["blerp", "djoozn", "ferglerb"]}
        response = self.client.post(
            reverse("api_game_list"), data=json.dumps(gogids), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content.decode())
        self.assertEqual(len(games["results"]), 0)


class TestInstallerDraftApi(TestCase):
    """Test case for installer draft creation and moderation API"""

    def setUp(self):
        self.game = factories.GameFactory(name="Test Game", slug="test-game")
        self.runner = factories.RunnerFactory(name="Wine", slug="wine")
        self.user = factories.UserFactory(username="testuser")
        self.admin = factories.UserFactory(username="admin", is_staff=True)

        # Valid installer content
        self.valid_content = """game:
  exe: drive_c/game/game.exe
  prefix: $GAMEDIR/prefix
files:
  - setup: https://example.com/setup.exe
installer:
  - task:
      name: wineexec
      executable: setup
"""

    def test_anonymous_cannot_create_draft(self):
        """Anonymous users should not be able to create drafts"""
        response = self.client.post(
            reverse("api_installer_draft_list"),
            data=json.dumps(
                {
                    "game_slug": "test-game",
                    "runner": "wine",
                    "version": "Test",
                    "content": self.valid_content,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_create_draft(self):
        """Authenticated users should be able to create installer drafts"""
        self.client.login(username="testuser", password="password")
        response = self.client.post(
            reverse("api_installer_draft_list"),
            data=json.dumps(
                {
                    "game_slug": "test-game",
                    "runner": "wine",
                    "version": "Test Version",
                    "content": self.valid_content,
                    "draft": True,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content.decode())
        self.assertEqual(data["version"], "Test Version")
        self.assertTrue(data["draft"])

    def test_can_submit_for_review(self):
        """Users can submit installers for moderation review"""
        self.client.login(username="testuser", password="password")
        response = self.client.post(
            reverse("api_installer_draft_list"),
            data=json.dumps(
                {
                    "game_slug": "test-game",
                    "runner": "wine",
                    "version": "Review Version",
                    "content": self.valid_content,
                    "draft": False,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content.decode())
        self.assertFalse(data["draft"])

    def test_invalid_game_slug_rejected(self):
        """Creating a draft with invalid game slug should fail"""
        self.client.login(username="testuser", password="password")
        response = self.client.post(
            reverse("api_installer_draft_list"),
            data=json.dumps(
                {
                    "game_slug": "nonexistent-game",
                    "runner": "wine",
                    "version": "Test",
                    "content": self.valid_content,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_runner_rejected(self):
        """Creating a draft with invalid runner should fail"""
        self.client.login(username="testuser", password="password")
        response = self.client.post(
            reverse("api_installer_draft_list"),
            data=json.dumps(
                {
                    "game_slug": "test-game",
                    "runner": "invalid-runner",
                    "version": "Test",
                    "content": self.valid_content,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_yaml_rejected(self):
        """Creating a draft with invalid YAML should fail"""
        self.client.login(username="testuser", password="password")
        response = self.client.post(
            reverse("api_installer_draft_list"),
            data=json.dumps(
                {
                    "game_slug": "test-game",
                    "runner": "wine",
                    "version": "Test",
                    "content": "invalid: yaml: content:",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_can_accept_submission(self):
        """Admins should be able to accept submissions"""
        # Create a submission (not a draft)
        draft = factories.InstallerDraftFactory(
            game=self.game,
            runner=self.runner,
            user=self.user,
            version="Submitted Version",
            content=self.valid_content,
            draft=False,
        )

        self.client.login(username="admin", password="password")
        response = self.client.post(
            reverse("api_installer_draft_accept", kwargs={"pk": draft.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Draft should be deleted after acceptance
        self.assertFalse(models.InstallerDraft.objects.filter(pk=draft.pk).exists())
        # Installer should be created
        self.assertTrue(
            models.Installer.objects.filter(game=self.game, version="Submitted Version").exists()
        )

    def test_admin_can_reject_submission(self):
        """Admins should be able to reject submissions with feedback"""
        draft = factories.InstallerDraftFactory(
            game=self.game,
            runner=self.runner,
            user=self.user,
            version="Rejected Version",
            content=self.valid_content,
            draft=False,
        )

        self.client.login(username="admin", password="password")
        response = self.client.post(
            reverse("api_installer_draft_reject", kwargs={"pk": draft.pk}),
            data=json.dumps({"review": "Missing wine version specification"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Draft should still exist but be set back to draft status
        draft.refresh_from_db()
        self.assertTrue(draft.draft)
        self.assertEqual(draft.review, "Missing wine version specification")

    def test_reject_requires_review_message(self):
        """Rejecting without review feedback should fail"""
        draft = factories.InstallerDraftFactory(
            game=self.game,
            runner=self.runner,
            user=self.user,
            draft=False,
        )

        self.client.login(username="admin", password="password")
        response = self.client.post(
            reverse("api_installer_draft_reject", kwargs={"pk": draft.pk}),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_accept_draft_not_submitted(self):
        """Cannot accept a draft that hasn't been submitted for review"""
        draft = factories.InstallerDraftFactory(
            game=self.game,
            runner=self.runner,
            user=self.user,
            draft=True,  # Still a draft, not submitted
        )

        self.client.login(username="admin", password="password")
        response = self.client.post(
            reverse("api_installer_draft_accept", kwargs={"pk": draft.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_non_admin_cannot_accept(self):
        """Non-admin users should not be able to accept submissions"""
        draft = factories.InstallerDraftFactory(
            game=self.game,
            runner=self.runner,
            user=self.user,
            draft=False,
        )

        self.client.login(username="testuser", password="password")
        response = self.client.post(
            reverse("api_installer_draft_accept", kwargs={"pk": draft.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)


class TestGameSubmissionSpamAssessment(TestCase):
    """The submissions API reports an advisory spam assessment to moderators"""

    def setUp(self):
        self.admin = factories.UserFactory(username="spam-admin", is_staff=True)
        self.client.force_login(self.admin)
        self.url = reverse("api_game_submissions")

    def create_submission(self, game_name, **user_kwargs):
        user = factories.UserFactory(**user_kwargs)
        game = factories.GameFactory(name=game_name)
        return models.GameSubmission.objects.create(user=user, game=game)

    def get_results(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return response.json()["results"]

    @skipUnless(antispam.is_available(), "lutris-antispam is not installed")
    def test_submission_carries_an_assessment(self):
        self.create_submission("Quake")
        (result,) = self.get_results()
        self.assertIn("spam_assessment", result)
        self.assertEqual(result["spam_assessment"]["verdict"], "clean")

    @skipUnless(antispam.is_available(), "lutris-antispam is not installed")
    def test_spam_submission_is_flagged(self):
        self.create_submission(
            "Slope Game Free", username="slopegamefree", email="slopegamefree@grr.la"
        )
        (result,) = self.get_results()
        self.assertEqual(result["spam_assessment"]["verdict"], "spam")
        self.assertIn(
            "email.disposable_domain",
            [rule["rule"] for rule in result["spam_assessment"]["matched_rules"]],
        )

    @skipUnless(antispam.is_available(), "lutris-antispam is not installed")
    def test_results_can_be_filtered_by_verdict(self):
        self.create_submission("Quake")
        self.create_submission(
            "Slope Game Free", username="slopegamefree", email="slopegamefree@grr.la"
        )
        self.assertEqual(len(self.get_results()), 2)
        spam = self.get_results(verdict="spam")
        self.assertEqual(len(spam), 1)
        self.assertEqual(spam[0]["game"]["name"], "Slope Game Free")

    def test_scoring_failure_does_not_break_the_queue(self):
        self.create_submission("Quake")
        with patch.object(antispam, "assess", side_effect=ValueError("boom")):
            (result,) = self.get_results()
        self.assertIsNone(result["spam_assessment"])

    def test_no_assessment_when_package_is_missing(self):
        self.create_submission("Quake")
        with patch.object(antispam, "assess", None):
            (result,) = self.get_results()
        self.assertIsNone(result["spam_assessment"])


class TestGameSubmissionBan(TestCase):
    """Rejecting a submission can also ban the submitter"""

    def setUp(self):
        self.admin = factories.UserFactory(username="ban-admin", is_staff=True)
        self.client.force_login(self.admin)
        self.spammer = factories.UserFactory(username="spammer", email="spam@grr.la")
        self.game = factories.GameFactory(name="Slope Game Free", is_public=False)
        self.submission = models.GameSubmission.objects.create(user=self.spammer, game=self.game)
        self.url = reverse(
            "api_game_submission_accept", kwargs={"submission_id": self.submission.id}
        )

    def test_reject_without_ban_leaves_the_user_alone(self):
        response = self.client.post(
            self.url, json.dumps({"accepted": False}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["banned"])
        self.spammer.refresh_from_db()
        self.assertTrue(self.spammer.is_active)
        self.assertEqual(self.spammer.username, "spammer")

    def test_reject_and_ban_deactivates_the_submitter(self):
        response = self.client.post(
            self.url,
            json.dumps({"accepted": False, "ban": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["banned"])
        self.spammer.refresh_from_db()
        self.assertFalse(self.spammer.is_active)
        self.assertEqual(self.spammer.email, "")
        self.assertNotEqual(self.spammer.username, "spammer")
        self.assertFalse(models.GameSubmission.objects.filter(pk=self.submission.pk).exists())
        self.assertFalse(models.Game.objects.filter(pk=self.game.pk).exists())

    def test_ban_records_who_was_banned(self):
        self.client.post(
            self.url,
            json.dumps({"accepted": False, "ban": True}),
            content_type="application/json",
        )
        log = KeyValueStore.objects.filter(key="banned_submitter").last()
        self.assertIsNotNone(log)
        self.assertIn("spammer", log.value)
        self.assertIn("spam@grr.la", log.value)
        self.assertIn("ban-admin", log.value)

    def test_ban_keeps_a_published_game(self):
        self.game.is_public = True
        self.game.save()
        self.client.post(
            self.url,
            json.dumps({"accepted": False, "ban": True}),
            content_type="application/json",
        )
        self.assertTrue(models.Game.objects.filter(pk=self.game.pk).exists())

    def test_staff_cannot_be_banned(self):
        self.spammer.is_staff = True
        self.spammer.save()
        response = self.client.post(
            self.url,
            json.dumps({"accepted": False, "ban": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.spammer.refresh_from_db()
        self.assertTrue(self.spammer.is_active)
        self.assertTrue(models.GameSubmission.objects.filter(pk=self.submission.pk).exists())

    def test_non_staff_cannot_ban(self):
        self.client.force_login(factories.UserFactory(username="regular"))
        response = self.client.post(
            self.url,
            json.dumps({"accepted": False, "ban": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.spammer.refresh_from_db()
        self.assertTrue(self.spammer.is_active)


class TestSpamDomainRecording(TestCase):
    """Banning a submitter banks the websites it was pushing"""

    def setUp(self):
        self.admin = factories.UserFactory(username="domain-admin", is_staff=True)
        self.client.force_login(self.admin)

    def ban_submission_for(self, website, profile_website=""):
        spammer = factories.UserFactory(
            username="spammer-%s" % models.SpamDomain.objects.count(),
            website=profile_website,
        )
        game = factories.GameFactory(name="Spam Game", website=website, is_public=False)
        submission = models.GameSubmission.objects.create(user=spammer, game=game)
        url = reverse("api_game_submission_accept", kwargs={"submission_id": submission.id})
        return self.client.post(
            url, json.dumps({"accepted": False, "ban": True}), content_type="application/json"
        )

    def test_ban_records_the_submitted_website(self):
        self.ban_submission_for("https://www.spam-example.com/page")
        self.assertTrue(models.SpamDomain.objects.filter(domain="spam-example.com").exists())

    def test_ban_records_the_profile_website(self):
        self.ban_submission_for("", profile_website="https://promo-example.net")
        self.assertTrue(models.SpamDomain.objects.filter(domain="promo-example.net").exists())

    def test_repeat_domain_increments_the_count(self):
        self.ban_submission_for("https://spam-example.com/one")
        self.ban_submission_for("https://spam-example.com/two")
        domain = models.SpamDomain.objects.get(domain="spam-example.com")
        self.assertEqual(domain.submission_count, 2)

    def test_shared_hosts_are_never_recorded(self):
        self.ban_submission_for("https://spammer.itch.io/game")
        self.ban_submission_for("https://github.com/spammer/repo")
        self.assertFalse(models.SpamDomain.objects.exists())

    def test_nothing_is_recorded_without_the_rules_package(self):
        # Without the package a shared host can't be told apart from a spam
        # domain, and recording blindly would poison the table.
        with patch.object(antispam, "is_shared_host", None):
            self.ban_submission_for("https://spam-example.com/one")
        self.assertFalse(models.SpamDomain.objects.exists())

    @skipUnless(antispam.is_available(), "lutris-antispam is not installed")
    def test_a_recorded_domain_is_scored_on_the_next_submission(self):
        self.ban_submission_for("https://spam-example.com/one")
        later = models.GameSubmission.objects.create(
            user=factories.UserFactory(username="another"),
            game=factories.GameFactory(
                name="Innocent Looking Title", website="https://spam-example.com/two"
            ),
        )
        assessment = antispam.assess_submission(later, library_game_count=0)
        self.assertIn(
            "history.known_spam_domain", [hit["rule"] for hit in assessment["matched_rules"]]
        )


@override_settings(SEND_EMAILS=True)
class TestBanEmail(TestCase):
    """Banning a submitter tells them their account was closed"""

    def setUp(self):
        self.admin = factories.UserFactory(username="mail-admin", is_staff=True)
        self.client.force_login(self.admin)
        self.spammer = factories.UserFactory(username="mailed-spammer", email="spam@example.net")
        self.game = factories.GameFactory(name="Slope Game Free", is_public=False)
        self.submission = models.GameSubmission.objects.create(user=self.spammer, game=self.game)
        self.url = reverse(
            "api_game_submission_accept", kwargs={"submission_id": self.submission.id}
        )

    def ban(self):
        return self.client.post(
            self.url,
            json.dumps({"accepted": False, "ban": True}),
            content_type="application/json",
        )

    def test_ban_emails_the_account(self):
        mail.outbox = []
        self.ban()
        # The address is captured before deactivate() blanks it
        sent = [message for message in mail.outbox if message.to == ["spam@example.net"]]
        self.assertEqual(len(sent), 1)
        self.assertIn("Lutris account", sent[0].subject)
        self.assertIn("mailed-spammer", sent[0].body)

    def test_plain_reject_sends_nothing(self):
        mail.outbox = []
        self.client.post(self.url, json.dumps({"accepted": False}), content_type="application/json")
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(ANTISPAM_BAN_EMAIL=False)
    def test_the_email_can_be_turned_off(self):
        mail.outbox = []
        response = self.ban()
        self.assertTrue(response.json()["banned"])
        self.assertEqual(len(mail.outbox), 0)

    def test_a_failing_email_does_not_leave_the_account_unbanned(self):
        with patch("games.views.games.send_account_banned", side_effect=OSError("smtp down")):
            response = self.ban()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["banned"])
        self.spammer.refresh_from_db()
        self.assertFalse(self.spammer.is_active)


@override_settings(SEND_EMAILS=True)
class TestBanFailureHandling(TestCase):
    """A ban either happens completely or not at all"""

    def setUp(self):
        self.admin = factories.UserFactory(username="atomic-admin", is_staff=True)
        self.client.force_login(self.admin)
        self.spammer = factories.UserFactory(username="atomic-spammer", email="spam@example.org")
        self.game = factories.GameFactory(name="Spam Title", is_public=False)
        self.submission = models.GameSubmission.objects.create(user=self.spammer, game=self.game)
        self.url = reverse(
            "api_game_submission_accept", kwargs={"submission_id": self.submission.id}
        )

    def ban(self):
        return self.client.post(
            self.url,
            json.dumps({"accepted": False, "ban": True}),
            content_type="application/json",
        )

    def test_ban_works_without_a_game_library(self):
        """Accounts with no library row must still be bannable.

        deactivate() raised RelatedObjectDoesNotExist on them in production,
        after the submission had already been deleted.
        """
        GameLibrary.objects.filter(user=self.spammer).delete()
        response = self.ban()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["banned"])
        self.spammer.refresh_from_db()
        self.assertFalse(self.spammer.is_active)

    def test_a_failure_leaves_nothing_half_done(self):
        with patch.object(User, "deactivate", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.ban()
        self.spammer.refresh_from_db()
        self.assertTrue(self.spammer.is_active)
        self.assertTrue(models.GameSubmission.objects.filter(pk=self.submission.pk).exists())
        self.assertTrue(models.Game.objects.filter(pk=self.game.pk).exists())
        self.assertFalse(BannedAccount.objects.filter(username="atomic-spammer").exists())
        self.assertFalse(models.SpamDomain.objects.exists())

    def test_a_failed_ban_does_not_email_the_account(self):
        mail.outbox = []
        with patch.object(User, "deactivate", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.ban()
        # Django mails the admins about the 500; the account must hear nothing
        to_account = [m for m in mail.outbox if m.to == ["spam@example.org"]]
        self.assertEqual(to_account, [])


@override_settings(SEND_EMAILS=True)
class TestBanningTheSameSpammerTwice(TestCase):
    """A spammer usually submits more than one game"""

    def setUp(self):
        self.admin = factories.UserFactory(username="repeat-admin", is_staff=True)
        self.client.force_login(self.admin)
        self.spammer = factories.UserFactory(username="repeat-spammer", email="spam@example.com")
        self.submissions = []
        for index in range(2):
            game = factories.GameFactory(
                name="Spam Title %s" % index,
                website="https://spam-%s.example" % index,
                is_public=False,
            )
            self.submissions.append(
                models.GameSubmission.objects.create(user=self.spammer, game=game)
            )

    def ban(self, submission):
        return self.client.post(
            reverse("api_game_submission_accept", kwargs={"submission_id": submission.id}),
            json.dumps({"accepted": False, "ban": True}),
            content_type="application/json",
        )

    def test_one_ban_clears_every_submission_from_that_account(self):
        self.assertTrue(self.ban(self.submissions[0]).json()["banned"])
        # Both submissions go, and both websites are remembered as spam
        self.assertFalse(models.GameSubmission.objects.filter(user=self.spammer).exists())
        self.assertTrue(models.SpamDomain.objects.filter(domain="spam-0.example").exists())
        self.assertTrue(models.SpamDomain.objects.filter(domain="spam-1.example").exists())
        # recorded and emailed exactly once
        self.assertEqual(BannedAccount.objects.filter(user=self.spammer).count(), 1)

    def test_banning_an_already_banned_account_adds_no_bookkeeping(self):
        """Reachable for accounts deactivated by other means, e.g. clear_spammers."""
        self.spammer.deactivate()
        mail.outbox = []
        response = self.ban(self.submissions[1])
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["banned"])
        self.assertFalse(models.GameSubmission.objects.filter(pk=self.submissions[1].pk).exists())
        self.assertEqual(BannedAccount.objects.filter(user=self.spammer).count(), 0)
        self.assertEqual(mail.outbox, [])

    def test_the_first_ban_is_recorded_normally(self):
        self.ban(self.submissions[0])
        record = BannedAccount.objects.get(user=self.spammer)
        self.assertEqual(record.email, "spam@example.com")
        self.assertEqual(record.username, "repeat-spammer")


class TestSpamDomainLimits(TestCase):
    def test_absurdly_long_hostnames_are_skipped(self):
        """Longer than the column: storing it would abort the ban with DataError."""
        self.assertIsNone(SpamDomain.record("http://" + "a" * 300 + ".com/x"))
        self.assertFalse(SpamDomain.objects.exists())

    def test_normal_hostnames_are_still_recorded(self):
        self.assertIsNotNone(SpamDomain.record("http://spam-example.com/x"))
        self.assertTrue(SpamDomain.objects.filter(domain="spam-example.com").exists())


@override_settings(SEND_EMAILS=True)
class TestBannedAccountsLeaveTheQueue(TestCase):
    """A banned account must not leave work in the moderation queue.

    Accepting a leftover submission published the game and then raised
    ValueError from the mail backend, because deactivate() blanks the address.
    """

    def setUp(self):
        self.admin = factories.UserFactory(username="queue-admin", is_staff=True)
        self.client.force_login(self.admin)
        self.spammer = factories.UserFactory(username="queue-spammer", email="spam@example.net")
        self.first, self.second = [
            models.GameSubmission.objects.create(
                user=self.spammer,
                game=factories.GameFactory(name="Spam %s" % index, is_public=False),
            )
            for index in range(2)
        ]

    def ban(self, submission):
        return self.client.post(
            reverse("api_game_submission_accept", kwargs={"submission_id": submission.id}),
            json.dumps({"accepted": False, "ban": True}),
            content_type="application/json",
        )

    def test_banning_clears_the_rest_of_that_account_queue(self):
        self.ban(self.first)
        self.assertFalse(models.GameSubmission.objects.filter(user=self.spammer).exists())
        self.assertFalse(models.Game.objects.filter(pk=self.second.game.pk).exists())

    def test_the_queue_hides_submissions_from_banned_accounts(self):
        self.spammer.deactivate()
        response = self.client.get(reverse("api_game_submissions"))
        listed = [row["id"] for row in response.json()["results"]]
        self.assertNotIn(self.first.id, listed)
        self.assertNotIn(self.second.id, listed)
