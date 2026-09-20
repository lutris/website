import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts import forms, sso
from accounts.models import BannedAccount, User
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

    def test_taken_username_does_not_crash_registration(self):
        """A username taken between validation and insert must not 500.

        RegistrationForm.save() swallows that IntegrityError and returns an
        unsaved user; anything that then saves it raises "Cannot force an update
        in save() with no primary key".
        """
        unsaved = User(username="racer", email="racer@example.net")
        with patch.object(forms.RegistrationForm, "save", return_value=unsaved):
            response = self.client.post(
                reverse("register"),
                {
                    "username": "racer",
                    "email": "racer@example.net",
                    "password1": "testpassword",
                    "password2": "testpassword",
                },
                REMOTE_ADDR="203.0.113.9",
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")


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


class TestLibrarySync(TestCase):
    def setUp(self):
        self.user = create_user(username="syncuser", password="password")
        self.client.force_login(self.user)
        self.url = reverse("api_user_library")

    def post_library(self, payload):
        return self.client.post(self.url, json.dumps(payload), content_type="application/json")

    def test_sync_accepts_list_of_games(self):
        game = {
            "name": "Quake",
            "slug": "quake",
            "runner": "linux",
            "platform": "Linux",
            "service": "",
            "service_id": "",
            "lastplayed": 0,
            "playtime": 0,
        }
        response = self.post_library([game])
        self.assertEqual(response.status_code, 200)

    def test_sync_rejects_object_payload(self):
        response = self.post_library({"slug": "quake"})
        self.assertEqual(response.status_code, 400)

    def test_sync_rejects_list_of_strings(self):
        response = self.post_library(["quake"])
        self.assertEqual(response.status_code, 400)


class TestSSO(TestCase):
    def test_redirect_url(self):
        url = sso.redirect_url("nonce", "secret", "user@domain.com", "external_id", "username")
        self.assertIn("/session/sso_login", url)
        self.assertIn("sso=", url)
        self.assertIn("sig=", url)


class TestBannedAccounts(TestCase):
    """A banned email cannot be used to register again"""

    def setUp(self):
        self.banned = BannedAccount.objects.create(email="spammer@example.net", username="spammer")

    def test_banned_email_is_refused_at_registration(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "spammer2",
                "email": "spammer@example.net",
                "password1": "testpassword",
                "password2": "testpassword",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="spammer2").exists())
        self.assertContains(response, "cannot be used to register")

    def test_banned_email_check_ignores_case_and_spacing(self):
        self.assertTrue(BannedAccount.is_email_banned(" Spammer@Example.NET "))
        self.assertFalse(BannedAccount.is_email_banned("someone@example.net"))
        self.assertFalse(BannedAccount.is_email_banned(""))

    def test_other_emails_still_register(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "legit",
                "email": "legit@example.net",
                "password1": "testpassword",
                "password2": "testpassword",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="legit").exists())

    def test_signup_ip_is_recorded(self):
        self.client.post(
            reverse("register"),
            {
                "username": "tracked",
                "email": "tracked@example.net",
                "password1": "testpassword",
                "password2": "testpassword",
            },
            REMOTE_ADDR="203.0.113.7",
        )
        user = User.objects.get(username="tracked")
        self.assertEqual(user.signup_ip, "203.0.113.7")
