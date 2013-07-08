from django.test import TestCase
from . import factories
import json


class ApiTest(TestCase):
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
