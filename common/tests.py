# pylint: disable=missing-docstring
from django.test import TestCase

from common.util import clean_html, extract_domain, romkan, slugify


class PagesTest(TestCase):
    def test_get_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        response = self.client.get("/foobar/baz")
        self.assertEqual(response.status_code, 404)


class TestUtils(TestCase):
    def test_slugify(self):
        self.assertEqual(slugify(None), "")
        self.assertEqual(slugify("Foo bar"), "foo-bar")
        if romkan:
            self.assertEqual(slugify("わがままアリスと百日戦争"), "wagamamaarisuto")
        else:
            print("Romkan not installed")
        self.assertEqual(
            slugify("关于我被小学女生绑架这件事"),
            "guan-yu-wo-bei-xiao-xue-nv-sheng-bang-jia-zhe-jian",
        )

    def test_clean_html(self):
        dirty_markup = "This is <b> a string </b> with <span>tags</span>"
        self.assertEqual(clean_html(dirty_markup), "This is <b> a string </b> with tags")

    def test_clean_html_keeps_links(self):
        dirty_markup = (
            '<div v-if="foo" class="blue">Visit '
            '<a href="https://lutris.net">Lutris.net</a> </div>'
            "<br/><p>it's full of <blink>fun</blink>!</p>"
        )
        self.assertEqual(
            clean_html(dirty_markup),
            'Visit <a href="https://lutris.net">Lutris.net</a> it\'s full of fun!',
        )


class TestExtractDomain(TestCase):
    def test_extracts_the_bare_domain(self):
        self.assertEqual(extract_domain("https://www.Example.com/page"), "example.com")
        self.assertEqual(extract_domain("example.com"), "example.com")
        self.assertEqual(extract_domain("http://sub.example.co.uk:8080/x"), "sub.example.co.uk")
        self.assertEqual(extract_domain("https://user:pw@spam.io/a"), "spam.io")

    def test_returns_empty_for_things_that_are_not_domains(self):
        self.assertEqual(extract_domain(""), "")
        self.assertEqual(extract_domain(None), "")
        self.assertEqual(extract_domain("just some words"), "")

    def test_malformed_urls_do_not_raise(self):
        """Submitted websites are arbitrary text.

        An unmatched "[" makes urlparse raise "Invalid IPv6 URL", which took out
        scoring for the whole submission and mailed an error report per render.
        """
        for malformed in ("http://[", "foo[bar].com", "[", "https://exa[mple.com/x"):
            self.assertEqual(extract_domain(malformed), "", malformed)
