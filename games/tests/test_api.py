"""Test cases for game API"""
import json
import logging

from unittest.mock import MagicMock

from django.test import TestCase
from django.urls import reverse

from . import factories
from games import models
from providers.models import Provider, ProviderGame

LOGGER = logging.getLogger(__name__)


class TestGameApi(TestCase):
    """Test case for game API views"""

    def setUp(self):
        self.num_games = 10
        self.games = [
            factories.GameFactory(name='game_%d' % index, slug='game-%d' % index)
            for index in range(self.num_games)
        ]

    def test_can_get_games(self):
        """The API should return a list of games"""
        game_list_url = reverse('api_game_list')
        response = self.client.get(game_list_url)
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content.decode())
        self.assertEqual(len(games['results']), self.num_games)

    def test_can_get_subset_of_games(self):
        """The API should filter by a given list of game slugs"""
        game_slugs = {'games': ['game-1', 'game-2', 'game-4']}
        game_list_url = reverse('api_game_list')
        response = self.client.get(game_list_url, data=game_slugs,
                                   extra={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content.decode())
        self.assertEqual(len(games['results']), len(game_slugs['games']))

    def test_can_post_subset_of_games(self):
        """The API can use a POST request to query a list of games, allowing
        users to pass a longer list
        """
        game_slugs = {'games': ['game-1', 'game-2', 'game-4']}
        game_list_url = reverse('api_game_list')
        response = self.client.post(
            game_list_url,
            data=json.dumps(game_slugs),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content.decode())
        self.assertEqual(len(games['results']), len(game_slugs['games']))

    def test_can_query_game_details(self):
        """The API can return details about a game"""
        response = self.client.get(reverse('api_game_detail',
                                           kwargs={'slug': 'game-1'}))
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
        library_url = reverse('api_game_library', kwargs={"username": user.username})
        response = self.client.get(library_url)
        self.assertEqual(response.status_code, 401)

    def test_can_get_library(self):
        """Users should be logged in to access a library"""
        user = self.library.user
        self.client.login(username=user.username, password='password')
        library_url = reverse('api_game_library', kwargs={"username": user.username})
        response = self.client.get(library_url)
        self.assertEqual(response.status_code, 200)


class TestInstallerApi(TestCase):
    """Test case of installer API views"""
    def setUp(self):
        self.slug = 'strider'
        self.game = factories.GameFactory(name=self.slug)
        factories.RunnerFactory(name="Linux", slug='linux')
        platform = factories.PlatformFactory()
        platform.default_installer = {"game": {"rom": "foo"}, "runner": "linux"}
        platform.save()  # pylint: disable=no-member
        self.game.platforms.add(platform)

    def test_can_get_installer_list_for_a_game(self):
        """The API can return a list of installers for a game"""
        self.assertTrue(self.game.platforms.count())
        response = self.client.get(reverse('api_game_installer_list', kwargs={'slug': self.slug}))
        self.assertEqual(response.status_code, 200)

    def test_get_installers_list_filtered(self):
        """The API returns a list of installers by filter"""
        self.assertTrue(self.game.platforms.count())
        inst_mgr = models.Installer.objects
        inst_mgr.get_filtered = MagicMock()
        period_start = '2020-01-01T00:00:00'
        period_end = '2021-01-01T00:00:00'
        response = self.client.get(reverse('api_installer_list'), {
            'status': 'published',
            'revision': 'final',
            'created_from': period_start,
            'created_to': period_end,
            'updated_from': period_start,
            'updated_to': period_end,
        })
        inst_mgr.get_filtered.assert_called_with({
            'published': True,
            'draft': False,
            'created_from': period_start,
            'created_to': period_end,
            'updated_from': period_start,
            'updated_to': period_end,
        })
        self.assertEqual(response.status_code, 200)

    def test_get_installers_history_list_filtered(self):
        """The API returns a list of installers history by filter"""
        self.assertTrue(self.game.platforms.count())
        inst_mgr = models.InstallerHistory.objects
        inst_mgr.get_filtered = MagicMock()
        period_start = '2020-01-01T00:00:00'
        period_end = '2021-01-01T00:00:00'
        response = self.client.get(reverse('api_installer_history_list'), {
            'created_from': period_start,
            'created_to': period_end,
        })
        inst_mgr.get_filtered.assert_called_with({
            'created_from': period_start,
            'created_to': period_end,
        })
        self.assertEqual(response.status_code, 200)

    def test_can_get_installer_history_for_installer(self):
        """The API can return a history for a given installer"""
        response = self.client.get(reverse('api_installer_history', kwargs={'installer_id': 1307}))
        self.assertEqual(response.status_code, 200)


class TestGameProviderApi(TestCase):
    """Test case for 3rd party game services integration"""

    def setUp(self):
        self.games = [
            factories.GameFactory(
                name='game_%d' % index,
                slug='game-%d' % index,
                gogid=str(1234 + index)
            )

            for index in range(10)
        ]
        provider = Provider.objects.create(name="gog", website="https://gogdb.org")
        for game in self.games:
            provider_game = ProviderGame.objects.create(
                name=game.name,
                slug=game.gogid,
                provider=provider
            )
            game.provider_games.add(provider_game)

    def test_can_get_games_by_gogid(self):
        """The game list API can be queried by GOG ID"""
        gogids = {'gogid': ['1234', '1235', '1236']}
        response = self.client.post(
            reverse('api_game_list'),
            data=json.dumps(gogids),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        games = json.loads(response.content.decode())
        self.assertEqual(len(games['results']), 3)

    def test_can_receive_garbage_in_gogids(self):
        """The view should not crash when passed invalid GOG IDs"""
        gogids = {'gogid': ['blerp', 'djoozn', 'ferglerb']}
        response = self.client.post(
            reverse('api_game_list'),
            data=json.dumps(gogids),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content.decode())
        self.assertEqual(len(games['results']), 0)


class TestInstallerDraftApi(TestCase):
    """Test case for installer draft creation and moderation API"""

    def setUp(self):
        self.game = factories.GameFactory(name='Test Game', slug='test-game')
        self.runner = factories.RunnerFactory(name='Wine', slug='wine')
        self.user = factories.UserFactory(username='testuser')
        self.admin = factories.UserFactory(username='admin', is_staff=True)

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
            reverse('api_installer_draft_list'),
            data=json.dumps({
                'game_slug': 'test-game',
                'runner': 'wine',
                'version': 'Test',
                'content': self.valid_content,
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_create_draft(self):
        """Authenticated users should be able to create installer drafts"""
        self.client.login(username='testuser', password='password')
        response = self.client.post(
            reverse('api_installer_draft_list'),
            data=json.dumps({
                'game_slug': 'test-game',
                'runner': 'wine',
                'version': 'Test Version',
                'content': self.valid_content,
                'draft': True,
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content.decode())
        self.assertEqual(data['version'], 'Test Version')
        self.assertTrue(data['draft'])

    def test_can_submit_for_review(self):
        """Users can submit installers for moderation review"""
        self.client.login(username='testuser', password='password')
        response = self.client.post(
            reverse('api_installer_draft_list'),
            data=json.dumps({
                'game_slug': 'test-game',
                'runner': 'wine',
                'version': 'Review Version',
                'content': self.valid_content,
                'draft': False,
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content.decode())
        self.assertFalse(data['draft'])

    def test_invalid_game_slug_rejected(self):
        """Creating a draft with invalid game slug should fail"""
        self.client.login(username='testuser', password='password')
        response = self.client.post(
            reverse('api_installer_draft_list'),
            data=json.dumps({
                'game_slug': 'nonexistent-game',
                'runner': 'wine',
                'version': 'Test',
                'content': self.valid_content,
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_runner_rejected(self):
        """Creating a draft with invalid runner should fail"""
        self.client.login(username='testuser', password='password')
        response = self.client.post(
            reverse('api_installer_draft_list'),
            data=json.dumps({
                'game_slug': 'test-game',
                'runner': 'invalid-runner',
                'version': 'Test',
                'content': self.valid_content,
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_yaml_rejected(self):
        """Creating a draft with invalid YAML should fail"""
        self.client.login(username='testuser', password='password')
        response = self.client.post(
            reverse('api_installer_draft_list'),
            data=json.dumps({
                'game_slug': 'test-game',
                'runner': 'wine',
                'version': 'Test',
                'content': 'invalid: yaml: content:',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_can_accept_submission(self):
        """Admins should be able to accept submissions"""
        # Create a submission (not a draft)
        draft = factories.InstallerDraftFactory(
            game=self.game,
            runner=self.runner,
            user=self.user,
            version='Submitted Version',
            content=self.valid_content,
            draft=False,
        )

        self.client.login(username='admin', password='password')
        response = self.client.post(
            reverse('api_installer_draft_accept', kwargs={'pk': draft.pk}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Draft should be deleted after acceptance
        self.assertFalse(models.InstallerDraft.objects.filter(pk=draft.pk).exists())
        # Installer should be created
        self.assertTrue(models.Installer.objects.filter(
            game=self.game,
            version='Submitted Version'
        ).exists())

    def test_admin_can_reject_submission(self):
        """Admins should be able to reject submissions with feedback"""
        draft = factories.InstallerDraftFactory(
            game=self.game,
            runner=self.runner,
            user=self.user,
            version='Rejected Version',
            content=self.valid_content,
            draft=False,
        )

        self.client.login(username='admin', password='password')
        response = self.client.post(
            reverse('api_installer_draft_reject', kwargs={'pk': draft.pk}),
            data=json.dumps({'review': 'Missing wine version specification'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Draft should still exist but be set back to draft status
        draft.refresh_from_db()
        self.assertTrue(draft.draft)
        self.assertEqual(draft.review, 'Missing wine version specification')

    def test_reject_requires_review_message(self):
        """Rejecting without review feedback should fail"""
        draft = factories.InstallerDraftFactory(
            game=self.game,
            runner=self.runner,
            user=self.user,
            draft=False,
        )

        self.client.login(username='admin', password='password')
        response = self.client.post(
            reverse('api_installer_draft_reject', kwargs={'pk': draft.pk}),
            data=json.dumps({}),
            content_type='application/json'
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

        self.client.login(username='admin', password='password')
        response = self.client.post(
            reverse('api_installer_draft_accept', kwargs={'pk': draft.pk}),
            content_type='application/json'
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

        self.client.login(username='testuser', password='password')
        response = self.client.post(
            reverse('api_installer_draft_accept', kwargs={'pk': draft.pk}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
