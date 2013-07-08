from django.test import TestCase


class ApiTest(TestCase):
    def test_get_library(self):
        response = self.client.get("/api/v1/library/")
        self.assertContains(response, "")
