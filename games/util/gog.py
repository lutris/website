"""GOG related utilities"""
import os
import logging
import requests
from django.conf import settings

from common.util import crop_banner

LOGGER = logging.getLogger(__name__)


def download_logo(gog_game, dest_path, formatter="398_2x"):
    """Downloads all game logos from GOG

    Args:
        gog_game (dict): GOG game details from the API
        dest_path (str): where to save the logo
        formatter (str): Image size to download. Other used
                         values on the GOG website are 256 and 195
    """
    response = requests.get("https:%s_product_tile_%s.jpg" % (gog_game["image"], formatter))
    with open(dest_path, "wb") as logo_file:
        logo_file.write(response.content)
    LOGGER.info("Saved image for %s to %s", gog_game["slug"], dest_path)


def get_logo(gog_game, formatter="398_2x"):
    """Return the content of the GOG logo (cropped to Lutris ratio)"""
    logo_filename = "%s_%s.jpg" % (gog_game["id"], formatter)

    # Get the logo from GOG
    gog_logo_path = os.path.join(settings.GOG_LOGO_PATH, logo_filename)
    if not os.path.exists(gog_logo_path):
        download_logo(gog_game, gog_logo_path)

    # Cropping the logo to lutris dimensions
    logo_path = os.path.join(settings.GOG_LUTRIS_LOGO_PATH, logo_filename)
    if not os.path.exists(logo_path):
        LOGGER.info("Cropping %s", logo_path)
        crop_banner(os.path.join(settings.GOG_LOGO_PATH, logo_filename), logo_path)
    with open(logo_path, 'rb') as logo_file:
        content = logo_file.read()
    return content
