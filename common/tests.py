# pylint: disable=missing-docstring
from django.test import TestCase
from common.util import slugify, clean_html


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
        self.assertEqual(
            slugify("关于我被小学女生绑架这件事"),
            "guan-yu-wo-bei-xiao-xue-nv-sheng-bang-jia-zhe-jian"
        )

    def test_clean_html(self):
        dirty_markup = "This is <b> a string </b> with <span>tags</span>"
        self.assertEqual(clean_html(dirty_markup), "This is <b> a string </b> with tags")

    def test_clean_html_keeps_links(self):
        dirty_markup = (
            "<div v-if=\"foo\" class=\"blue\">Visit "
            "<a href=\"https://lutris.net\">Lutris.net</a> </div>"
            "<br/><p>it's full of <blink>fun</blink>!</p>"
        )
        self.assertEqual(
            clean_html(dirty_markup),
            "Visit <a href=\"https://lutris.net\">Lutris.net</a> it's full of fun!"
        )
