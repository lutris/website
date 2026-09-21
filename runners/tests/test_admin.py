from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from games.tests import factories


class TestRunnerAdmin(TestCase):
    def setUp(self):
        self.runner = factories.RunnerFactory(name="Linux")
        self.user = factories.UserFactory(is_staff=True)
        self.client.force_login(self.user)

    def test_view_only_staff_can_open_runner_change_page(self):
        self.user.user_permissions.add(Permission.objects.get(codename="view_runner"))
        response = self.client.get(reverse("admin:runners_runner_change", args=[self.runner.id]))
        self.assertEqual(response.status_code, 200)
