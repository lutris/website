from mock import patch
from games.util import steam
from django.test import TestCase


class SteamMock():
    status_code = 200

    def json(self):
        return {'response': {'games': [
            {
                'appid': 440,
                'has_community_visible_stats': True,
                'img_icon_url': 'e3f595a92552da3d664ad00277fad2107345f743',
                'img_logo_url': '07385eb55b5ba974aebbe74d3c99626bda7920b8',
                'name': u'Team Fortress 2',
                'playtime_forever': 1315},
            {
                'appid': 570,
                'img_icon_url': '0bbb630d63262dd66d2fdd0f7d37e8661a410075',
                'img_logo_url': 'd4f836839254be08d8e9dd333ecc9a01782c26d2',
                'name': u'Dota 2',
                'playtime_forever': 75}
        ]}}


class TestSteamSync(TestCase):
    def test_sync(self):
        with patch('requests.get') as get_mock:
            get_mock.return_value = SteamMock()
            games = steam.steam_sync("123")
        self.assertEqual(len(games), 2)
        self.assertEqual(games[0]['appid'], 440)
        self.assertEqual(games[1]['name'], 'Dota 2')
