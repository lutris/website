from django.test import TestCase
from common.util import slugify


class PagesTest(TestCase):

    def test_get_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        response = self.client.get("/foobar/baz")
        self.assertEqual(response.status_code, 404)


class TestNewsFeed(TestCase):
    def test_feed_availability(self):
        response = self.client.get("/news/feed/")
        self.assertEqual(response.status_code, 200)


class TestUtils(TestCase):
    def test_slugify(self):
        self.assertEqual(slugify(None), "")
        self.assertEqual(slugify("Foo bar"), "foo-bar")
        self.assertEqual(slugify("わがままアリスと百日戦争"), "wagamamaarisuto")
