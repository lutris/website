from django.test import TestCase
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User


class TestRegistration(TestCase):
    def test_user_can_register(self):
        registration_url = reverse("register")
        response = self.client.get(registration_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(registration_url, {
            'username': "testuser",
            'password1': "testpassword",
            'password2': "testpassword"
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        created_user = User.objects.get(username="testuser")
        self.assertTrue(created_user)
