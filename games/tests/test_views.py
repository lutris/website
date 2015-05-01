import json
from django.test import TestCase
from django.core.urlresolvers import reverse
from . import factories


class TestInstallerViews(TestCase):
    def setUp(self):
        self.game = factories.GameFactory(name='doom', slug='doom')
        self.user = factories.UserFactory()

    def test_anonymous_user_cant_create_installer(self):
        factories.GameFactory()
        response = self.client.get(reverse("new_installer",
                                           kwargs={'slug': 'flashback'}),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("user/login", response.redirect_chain[0][0])

    def test_logged_in_user_can_create_installer(self):
        factories.UserFactory()

    def test_can_redirect_to_game_page_from_installer_slug(self):
        installer = factories.InstallerFactory(game=self.game)

        game_for_installer_url = reverse("game_for_installer",
                                         kwargs={'slug': installer.slug})
        response = self.client.get(game_for_installer_url)
        self.assertRedirects(
            response, reverse('game_detail', kwargs={'slug': self.game.slug})
        )

    def test_can_access_installer_feed(self):
        response = self.client.get('/games/installer/feed/')
        self.assertEqual(response.status_code, 200)

    def test_can_get_installer_list_as_json(self):
        factories.InstallerFactory(
            game=self.game,
            slug='doom-dos',
            version='dos',
        )
        factories.InstallerFactory(
            game=self.game,
            slug='doom-zdoom',
            version='zdoom',
        )
        installer_url = reverse('get_installers', kwargs={'slug': 'doom'})
        response = self.client.get(installer_url)
        self.assertEqual(response.status_code, 200)
        installers = json.loads(response.content)
        self.assertEqual(len(installers), 2)
        installer_slugs = [i['installer_slug'] for i in installers]
        self.assertIn('doom-zdoom', installer_slugs)
        self.assertIn('doom-dos', installer_slugs)


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

    def test_can_query_game_details(self):
        response = self.client.get(reverse('api_game_detail',
                                           kwargs={'slug': 'game-1'}))
        self.assertEqual(response.status_code, 200)
