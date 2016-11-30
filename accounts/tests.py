import json
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from common.util import create_admin, create_user


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
        self.assertTrue(created_user.gamelibrary)


class TestProfileView(TestCase):
    def setUp(self):
        self.username = 'datuser'
        self.password = 'password'
        self.user = create_user(username=self.username, password=self.password)

    def test_user_can_view_profile(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse("user_account",
                                           args=(self.user.username, )))
        self.assertEqual(response.status_code, 200)

    def test_profile_page_is_private(self):
        create_user(username='another', password='password')
        self.client.login(username='another', password='password')
        response = self.client.get(reverse("user_account",
                                           args=(self.user.username, )))
        self.assertEqual(response.status_code, 404)


class TestApiAuth(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_user_can_get_token(self):
        payload = {
            'username': 'admin',
            'password': 'admin'
        }
        response = self.client.post(reverse('accounts_get_token'), payload)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('token', response_data)
