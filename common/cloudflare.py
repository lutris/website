"""Cloudflare API utilities"""

import logging

import requests
from django.conf import settings

LOGGER = logging.getLogger(__name__)


def purge_urls(urls):
    """Purge a list of URLs from Cloudflare's cache"""
    zone_id = settings.CLOUDFLARE_ZONE_ID
    api_token = settings.CLOUDFLARE_API_TOKEN
    if not zone_id or not api_token:
        return
    try:
        response = requests.post(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache",
            headers={"Authorization": f"Bearer {api_token}"},
            json={"files": urls},
            timeout=10,
        )
        if not response.ok:
            LOGGER.error("Cloudflare purge failed: %s", response.text)
    except requests.RequestException as ex:
        LOGGER.error("Cloudflare purge request failed: %s", ex)
