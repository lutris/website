from django.test import TestCase
from django.core.urlresolvers import reverse


class TestEmailRendering(TestCase):
    def test_can_get_an_example_email(self):
        response = self.client.get(reverse('example_email'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Example email")
        self.assertContains(response, "The email title")
