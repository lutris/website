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
        library_url = reverse('api_game_library',
                              kwargs={'username': user.username})
        response = self.client.get(library_url)
        self.assertEqual(response.status_code, 401)

    def test_can_get_library(self):
        """Users should be logged in to access a library"""
        user = self.library.user
        self.client.login(username=user.username, password='password')
        library_url = reverse('api_game_library',
                              kwargs={'username': user.username})
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
