"""Email test suite"""

# pylint: disable=C0103
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from common.util import create_admin, create_user
from emails.messages import send_email


class TestEmailRendering(TestCase):
    """Test that emails get rendered by the website"""

    def setUp(self):
        self.user = create_user(username="user", password="password")
        self.admin = create_admin(username="admin", password="password")

    def test_can_get_an_example_email(self):
        """Test the email rendering view"""
        response = self.client.get(reverse("example_email"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Example email")
        self.assertContains(response, "The email title")

    def test_can_load_email_sender_if_admin(self):
        """Admin users should be able to send an email from the test page"""
        self.client.login(username="admin", password="password")
        response = self.client.get(reverse("email_sender_test"))
        self.assertEqual(response.status_code, 200)

    def test_regular_users_dont_have_access_to_tester(self):
        """Normal users should not be able to send an email from the test page"""
        self.client.login(username="user", password="password")
        response = self.client.get(reverse("email_sender_test"))
        self.assertEqual(response.status_code, 403)


@override_settings(SEND_EMAILS=True)
class TestSendEmailRecipients(TestCase):
    def test_blank_recipients_are_dropped(self):
        """A deactivated account has no address.

        Django raises ValueError("Invalid address") from inside the SMTP
        backend, past fail_silently, so an empty recipient must never get that
        far: it 500s the moderator after the action has already been committed.
        """
        self.assertEqual(send_email("account_banned", {"username": "x"}, "subject", ""), 0)
        self.assertEqual(send_email("account_banned", {"username": "x"}, "subject", [""]), 0)
        self.assertEqual(mail.outbox, [])

    def test_real_recipients_still_get_mail(self):
        send_email("account_banned", {"username": "x"}, "subject", "someone@example.net")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["someone@example.net"])
