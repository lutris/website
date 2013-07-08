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
