import json

from django.test import TestCase
from django.urls import reverse

from accounts import sso
from accounts.models import User
from common.util import create_admin, create_user


class TestRegistration(TestCase):
    def test_user_can_register(self):
        registration_url = reverse("register")
        response = self.client.get(registration_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            registration_url,
            {
                "username": "testuser",
                "email": "testuser@lutris.net",
                "password1": "testpassword",
                "password2": "testpassword",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        created_user = User.objects.get(username="testuser")
        self.assertTrue(created_user)
        self.assertEqual(created_user.email, "testuser@lutris.net")
        self.assertTrue(created_user.gamelibrary)


class TestProfileView(TestCase):
    def setUp(self):
        self.username = "datuser"
        self.password = "password"
        self.user = create_user(username=self.username, password=self.password)

    def test_user_can_view_profile(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse("user_account", args=(self.user.username,)))
        self.assertEqual(response.status_code, 200)

    def test_profile_page_is_private(self):
        create_user(username="another", password="password")
        self.client.login(username="another", password="password")
        response = self.client.get(reverse("user_account", args=(self.user.username,)))
        self.assertEqual(response.status_code, 404)


class TestApiAuth(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_user_can_get_token(self):
        payload = {"username": "admin", "password": "admin"}
        response = self.client.post(reverse("accounts_get_token"), payload)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode())
        self.assertIn("token", response_data)


class TestSSO(TestCase):
    def test_redirect_url(self):
        url = sso.redirect_url("nonce", "secret", "user@domain.com", "external_id", "username")
        self.assertIn("/session/sso_login", url)
        self.assertIn("sso=", url)
        self.assertIn("sig=", url)


class TestUsernameChange(TestCase):
    def setUp(self):
        self.username = "originaluser"
        self.password = "s3cur3pass"
        self.user = create_user(username=self.username, password=self.password)
        self.change_url = reverse("username_change")
        self.client.login(username=self.username, password=self.password)

    def test_get_renders_form(self):
        response = self.client.get(self.change_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_username_change")

    def test_valid_rename_succeeds(self):
        response = self.client.post(self.change_url, {"username": "newusername"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newusername")
        self.assertIsNotNone(self.user.username_changed_at)

    def test_duplicate_username_rejected(self):
        create_user(username="takenname", password="password")
        response = self.client.post(self.change_url, {"username": "takenname"})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "username", "A user with that username already exists.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, self.username)

    def test_same_username_accepted(self):
        response = self.client.post(self.change_url, {"username": self.username}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, self.username)

    def test_cooldown_blocks_second_change(self):
        from datetime import timedelta

        from django.utils import timezone

        # Simulate a recent username change (5 days ago)
        self.user.username_changed_at = timezone.now() - timedelta(days=5)
        self.user.save(update_fields=["username_changed_at"])

        response = self.client.post(self.change_url, {"username": "anotherusername"}, follow=True)
        # Should redirect back to profile_edit with an error
        self.assertRedirects(response, reverse("profile_edit"))
        messages_list = list(response.context["messages"])
        self.assertTrue(any("30 days" in str(m) for m in messages_list))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, self.username)

    def test_cooldown_expired_allows_change(self):
        from datetime import timedelta

        from django.utils import timezone

        # Simulate a username change 31 days ago (cooldown elapsed)
        self.user.username_changed_at = timezone.now() - timedelta(days=31)
        self.user.save(update_fields=["username_changed_at"])

        response = self.client.post(self.change_url, {"username": "freshusername"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "freshusername")

