from django.test import TestCase
from . import factories
from games import models


class TestGame(TestCase):
    def test_factory(self):
        game = factories.GameFactory(name="Quake 3 Arena", is_public=False)
        self.assertEqual(game.slug, "quake-3-arena")
        self.assertFalse(game.is_public)

    def test_website_url_no_website_specified(self):
        """
        Ensures that None is returned for website_url
        and website_url_hr if no website was specified
        """

        # Create a game with no website specified
        game = factories.GameFactory(name='Game Title', website='')

        # website_url should return None
        self.assertIsNone(game.website_url)

        # website_url_hr should return None
        self.assertIsNone(game.website_url_hr)

    def test_website_url_no_protocol_specified(self):
        """Ensures that URLs are uniform if no protocol was specified"""

        # Create a game with a protocol-less website (no http:// or https://)
        game = factories.GameFactory(name='Game Title', website='example.com')

        # If no protocol was specified, it should fall back to http://
        self.assertEqual(game.website_url, 'http://example.com')

        # HR URL should be unchanged
        self.assertEqual(game.website_url_hr, 'example.com')

    def test_website_url_http_specified(self):
        """Ensures that URLs are uniform if http was specified"""

        # Create a game with an http:// website specified
        game = factories.GameFactory(name='Game Title', website='http://example.com')

        # If a protocl was specified, it should be returned unchanged
        self.assertEqual(game.website_url, 'http://example.com')

        # HR URL should strip the http:// part
        self.assertEqual(game.website_url_hr, 'example.com')

    def test_website_url_https_specified(self):
        """Ensures that URLs are uniform if https was specified"""

        # Create a game with an https:// website specified
        game = factories.GameFactory(name='Game Title', website='https://example.com')

        # If a protocl was specified, it should be returned unchanged
        self.assertEqual(game.website_url, 'https://example.com')

        # HR URL should strip the https:// part
        self.assertEqual(game.website_url_hr, 'example.com')

    def test_website_url_strip_trailing_slash(self):
        """Ensures that trailing slashes are stripped for HR website_url"""

        # Create a game with a URL with trailing slash
        game = factories.GameFactory(name='Game Title', website='http://example.com/')

        # If a trailing slash was given, it should not be stripped for website_url
        self.assertEqual(game.website_url, 'http://example.com/')

        # HR URL should strip the http:// part and the trailing slash
        self.assertEqual(game.website_url_hr, 'example.com')

    def test_game_list_filters_game_with_no_installers(self):
        doom = factories.GameFactory(name="Doom")
        game_list = models.Game.objects.with_installer()
        self.assertNotIn(doom, game_list)

    def test_published_games_only_gets_with_installers(self):
        doom = factories.GameFactory(name="Doom")
        factories.InstallerFactory(game=doom, version="test")
        game_list = models.Game.objects.published()
        self.assertIn(doom, game_list)

        game_list = models.Game.objects.published()
        factories.InstallerFactory(game=doom, version="test2")
        self.assertEqual(len(game_list), 1)

    def test_game_can_return_a_default_installer(self):
        snes = factories.PlatformFactory(name='SNES')
        snes.default_installer = {
            'main_file': 'rom',
            'files': [{'rom': 'N/A'}],
            'installer': [{'merge': {'src': 'rom', 'dst': '$GAMEDIR'}}]
        }
        snes.save()
        super_mario_world = factories.GameFactory(name="Super Mario World")
        super_mario_world.platforms.add(snes)
        default_installers = super_mario_world.get_default_installers()
        self.assertTrue(default_installers)
        self.assertEqual(default_installers[0]['slug'],
                         'super-mario-world-snes')

        self.assertTrue(super_mario_world.has_installer())


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

        self.installer = models.Installer()
        self.installer.slug = 'doom-shareware'
        self.installer.version = 'shareware'
        self.installer.game = self.game
        self.installer.runner = self.runner
        self.installer.user = self.user
        self.installer.save()

    def test_can_access_full_dit_representation(self):
        installer_dict = self.installer.as_dict()
        self.assertEqual(installer_dict['name'], "Doom")
        self.assertEqual(installer_dict['runner'], "linux")

    def test_installer_can_be_rendered_as_json(self):
        json_data = self.installer.as_json()
        self.assertIn("\"runner\": \"linux\"", json_data)
        self.assertIn("\"installer_slug\": \"doom-shareware\"", json_data)


class TestPlatform(TestCase):
    def test_instanciation(self):
        platform = models.Platform()
        platform.name = 'Linux'
        platform.save()
        self.assertEqual(platform.slug, 'linux')
        self.assertEqual(platform.__unicode__(), 'Linux')


class TestCompany(TestCase):
    def test_instanciation(self):
        company = models.Company()
        company.name = 'id Software'
        company.save()
        self.assertEqual(company.slug, 'id-software')
        self.assertEqual(company.__unicode__(), 'id Software')


class TestGenre(TestCase):
    def test_instanciation(self):
        genre = models.Genre()
        genre.name = 'Platformer'
        genre.save()
        self.assertEqual(genre.slug, 'platformer')
        self.assertEqual(genre.__unicode__(), 'Platformer')
