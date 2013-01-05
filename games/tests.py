"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

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
