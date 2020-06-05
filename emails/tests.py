"""Email test suite"""
# pylint: disable=C0103
from django.test import TestCase
from django.urls import reverse
from common.util import create_admin, create_user


class TestEmailRendering(TestCase):
    """Test that emails get rendered by the website"""
    def setUp(self):
        self.user = create_user(username='user', password='password')
        self.admin = create_admin(username='admin', password='password')

    def test_can_get_an_example_email(self):
        """Test the email rendering view"""
        response = self.client.get(reverse('example_email'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Example email")
        self.assertContains(response, "The email title")

    def test_can_load_email_sender_if_admin(self):
        """Admin users should be able to send an email from the test page"""
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('email_sender_test'))
        self.assertEqual(response.status_code, 200)

    def test_regular_users_dont_have_access_to_tester(self):
        """
        Normal users should not be able to send an email from the test page
        """
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('email_sender_test'))
        self.assertEqual(response.status_code, 403)
