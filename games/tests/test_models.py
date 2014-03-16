from django.test import TestCase
from . import factories
from games import models


class TestGame(TestCase):
    def test_factory(self):
        game = factories.GameFactory(name="Quake 3 Arena", is_public=False)
        self.assertEqual(game.slug, "quake-3-arena")
        self.assertFalse(game.is_public)

    def test_game_list_filters_game_with_no_installers(self):
        doom = factories.GameFactory(name="Doom")
        game_list = models.Game.objects.published()
        self.assertNotIn(doom, game_list)

    def test_published_games_only_gets_with_installers(self):
        doom = factories.GameFactory(name="Doom")
        factories.InstallerFactory(game=doom, version="test")
        game_list = models.Game.objects.published()
        self.assertIn(doom, game_list)

        game_list = models.Game.objects.published()
        factories.InstallerFactory(game=doom, version="test2")
        self.assertEqual(len(game_list), 1)


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


class TestInstallers(TestCase):
    def setUp(self):
        self.game = factories.GameFactory(name="Doom")
        self.runner = factories.RunnerFactory(name='Linux')
        self.user = factories.UserFactory(first_name="test")

    def test_can_access_full_dit_representation(self):
        installer = models.Installer()
        installer.slug = 'doom-shareware'
        installer.version = 'shareware'
        installer.game = self.game
        installer.runner = self.runner
        installer.user = self.user
        installer.save()

        installer_dict = installer.as_dict()
        self.assertEqual(installer_dict['name'], "Doom")
        self.assertEqual(installer_dict['runner'], "linux")
