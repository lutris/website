from django.test import TestCase
from django.core.urlresolvers import reverse

from accounts.models import User


class TestRegistration(TestCase):
    def test_user_can_register(self):
        registration_url = reverse("register")
        response = self.client.get(registration_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(registration_url, {
            'username': "testuser",
            'email': 'admin@lutris.net',
            'password1': "testpassword",
            'password2': "testpassword"
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        created_user = User.objects.get(username="testuser")
        self.assertTrue(created_user)
        self.assertEqual(created_user.email, "admin@lutris.net")


class TestProfileView(TestCase):
    def test_user_can_view_profile(self):
        user = User.objects.create(username="dat-user")
        response = self.client.get(reverse("user_account",
                                           args=(user.username, )))
        self.assertEqual(response.status_code, 200)
