from django.test import TestCase
from django.core.urlresolvers import reverse
from . import factories
import json


class TestOldApi(TestCase):
    def setUp(self):
        game = factories.GameFactory
        games = [game() for i in range(5)]
        self.library = factories.GameLibraryFactory(games=games)
        other_games = [game(name="Metroid"), game(name="Mario")]
        self.other_library = factories.GameLibraryFactory(games=other_games)

    def test_anonymous_user_cant_get_library(self):
        response = self.client.get("/api/v1/library/")
        self.assertEqual(response.status_code, 401)

    def test_get_library(self):
        user = self.library.user
        self.assertTrue(user.api_key)

        response = self.client.get("/api/v1/library/?username=%s&api_key=%s"
                                   % (user.username, user.api_key.key))
        self.assertEqual(response.status_code, 200)
        library_games = json.loads(response.content)["objects"][0]['games']
        game_slugs = [game['slug'] for game in library_games]
        self.assertIn("quake", game_slugs)
        self.assertNotIn("mario", game_slugs)


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
        games = json.loads(response.content)
        self.assertEqual(len(games), self.num_games)

    def test_can_get_subset_of_games(self):
        game_slugs = {'games': ['game-1', 'game-2', 'game-4']}
        game_list_url = reverse('api_game_list')
        response = self.client.get(game_list_url, data=game_slugs,
                                   extra={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content)
        self.assertEqual(len(games), len(game_slugs['games']))

    def test_can_post_subset_of_games(self):
        game_slugs = {'games': ['game-1', 'game-2', 'game-4']}
        game_list_url = reverse('api_game_list')
        response = self.client.post(
            game_list_url,
            data=json.dumps(game_slugs),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        games = json.loads(response.content)
        self.assertEqual(len(games), len(game_slugs['games']))

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

    def test_can_get_library(self):
        user = self.library.user
        library_url = reverse('api_game_library',
                              kwargs={'username': user.username})
        response = self.client.get(library_url)
        self.assertEqual(response.status_code, 200)
