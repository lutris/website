from django.test import TestCase
from django.core.urlresolvers import reverse
from . import factories


class TestInstallerViews(TestCase):
    def test_anonymous_user_cant_create_installer(self):
        game = factories.GameFactory()
        response = self.client.get(reverse("new_installer",
                                           kwargs={'slug': game.slug}),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("user/login", response.redirect_chain[0][0])

    def test_logged_in_user_can_create_installer(self):
        user = factories.UserFactory()

    def test_can_redirect_to_game_page_from_installer_slug(self):
        game = factories.GameFactory(name="doom")
        installer = factories.InstallerFactory(game=game)

        game_for_installer_url = reverse("game_for_installer",
                                         kwargs={'slug': installer.slug})
        response = self.client.get(game_for_installer_url)
        self.assertRedirects(
            response, reverse('game_detail', kwargs={'slug': game.slug})
        )
