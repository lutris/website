from django.test import TestCase
from django.test.client import Client


class PagesTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        response = self.client.get("/foobar/baz")
        self.assertEqual(response.status_code, 404)
