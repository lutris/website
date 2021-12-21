"""Support for IDGB"""
import requests


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

    def get_games(self, page=1):
        """Iterate through all games"""
        return requests.post(
            self.base_url + "games/",
            data=(
                f"fields: *; sort updated_at asc;"
                f" limit {self.page_size};"
                f" offset {self.page_size * page - 1};"
            ),
            headers={
                "Client-ID": self.client_id,
                "Authorization": f"Bearer {self.access_token}"
            }
        )
