"""Support for IDGB"""
import requests

GAME_CATEGORIES = {
    0: "main_game",
    1: "dlc_addon",
    2: "expansion",
    3: "bundle",
    4: "standalone_expansion",
    5: "mod",
    6: "episode",
    7: "season",
    8: "remake",
    9: "remaster",
    10: "expanded_game",
    11: "port",
    12: "fork"
}


class IGDBClient:
    """API client for the IGDB API"""
    base_url = "https://api.igdb.com/v4/"
    page_size = 200

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None

    def get_authentication_token(self):
        """Request a new token from Twitch"""
        if not self.client_id:
            raise RuntimeError("No client ID set for Twitch")
        response = requests.post(
            "https://id.twitch.tv/oauth2/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }
        )
        self.access_token = response.json()["access_token"]
        return self.access_token

    def get_resources(self, url, page):
        """Generic method to access all API endpoints"""
        return requests.post(
            self.base_url + url,
            data=(
                f"fields: *; sort updated_at desc;"
                f" limit {self.page_size};"
                f" offset {self.page_size * page - 1};"
            ),
            headers={
                "Client-ID": self.client_id,
                "Authorization": f"Bearer {self.access_token}"
            }
        )
