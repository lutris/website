import json
import logging

from django.test import TestCase
from django.urls import reverse

from . import factories

LOGGER = logging.getLogger(__name__)


class TestGameApi(TestCase):
    def setUp(self):
        self.num_games = 10
        self.games = []
        for n in range(self.num_games):
            self.games.append(
                factories.GameFactory(name='game_%d' % n, slug='game-%d' % n)
            )

    def test_can_get_games(self):
        game_list_url = reverse('api_game_list')
        response = self.client.get(game_list_url)
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content.decode())
        self.assertEqual(len(games['results']), self.num_games)

    def test_can_get_subset_of_games(self):
        game_slugs = {'games': ['game-1', 'game-2', 'game-4']}
        game_list_url = reverse('api_game_list')
        response = self.client.get(game_list_url, data=game_slugs,
                                   extra={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content.decode())
        self.assertEqual(len(games['results']), len(game_slugs['games']))

    def test_can_post_subset_of_games(self):
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
        response = self.client.get(reverse('api_game_detail',
                                           kwargs={'slug': 'game-1'}))
        self.assertEqual(response.status_code, 200)


class TestGameLibraryApi(TestCase):
    def setUp(self):
        game = factories.GameFactory
        games = [game() for i in range(5)]
        self.library = factories.GameLibraryFactory(games=games)
        other_games = [game(name="Metroid"), game(name="Mario")]
        self.other_library = factories.GameLibraryFactory(games=other_games)

    def test_anonymous_requests_are_rejected(self):
        user = self.library.user
        library_url = reverse('api_game_library',
                              kwargs={'username': user.username})
        response = self.client.get(library_url)
        self.assertEqual(response.status_code, 401)

    def test_can_get_library(self):
        user = self.library.user
        self.client.login(username=user.username, password='password')
        library_url = reverse('api_game_library',
                              kwargs={'username': user.username})
        response = self.client.get(library_url)
        self.assertEqual(response.status_code, 200)


class TestInstallerApi(TestCase):
    def setUp(self):
        self.slug = 'strider'
        self.game = factories.GameFactory(name=self.slug)
        factories.RunnerFactory(name="Linux", slug='linux')
        platform = factories.PlatformFactory()
        platform.default_installer = {"game": {"rom": "foo"}, "runner": "linux"}
        platform.save()
        self.game.platforms.add(platform)

    def test_can_get_installer_list_for_a_game(self):
        self.assertTrue(self.game.platforms.count())
        response = self.client.get(reverse('api_game_installer_list', kwargs={'slug': self.slug}))
        self.assertEqual(response.status_code, 200)
