from django.test import TestCase
from . import factories


class ApiTest(TestCase):
    def setUp(self):
        games = [factories.GameFactory() for i in range(5)]
        self.library = factories.GameLibraryFactory(games=games)
        self.other_library = factories.GameLibraryFactory(games=games)

    def test_get_library(self):
        response = self.client.get("/api/v1/library/")
        #self.assertContains(response, "quake")
