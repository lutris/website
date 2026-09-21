from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from games.tests import factories


class TestGameAdmin(TestCase):
    def setUp(self):
        self.user = factories.UserFactory(is_staff=True)
        self.client.force_login(self.user)

    def test_view_only_staff_can_open_game_change_page(self):
        game = factories.GameFactory(name="Doom")
        self.user.user_permissions.add(Permission.objects.get(codename="view_game"))
        response = self.client.get(reverse("admin:games_game_change", args=[game.id]))
        self.assertEqual(response.status_code, 200)
