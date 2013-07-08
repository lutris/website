from django.test import TestCase
from . import factories


class TestGame(TestCase):
    def test_factory(self):
        game = factories.GameFactory(name="Quake 3 Arena")
        self.assertEqual(game.slug, "quake-3-arena")
        self.assertFalse(game.is_public)


class TestGameLibrary(TestCase):
    def test_library_generated_by_user(self):
        user = factories.UserFactory(first_name="test")

        library = user.gamelibrary
        self.assertEqual(len(library.games.all()), 0)
        for i in range(5):
            game = factories.GameFactory()
            library.games.add(game)

        self.assertEqual(len(library.games.all()), 5)

    def test_library_generated_by_factory(self):
        games = [factories.GameFactory() for i in range(5)]
        library = factories.GameLibraryFactory(games=games)
        self.assertEqual(len(library.games.all()), 5)
