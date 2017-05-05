import os
import re
import logging

import requests
from bs4 import BeautifulSoup
from PIL import Image
from django.conf import settings
from django.utils.text import slugify

from games.models import Company
from platforms.models import Platform


LOGGER = logging.getLogger(__name__)
API_URL = "http://thegamesdb.net/api/"
UNSUPPORTED_PLATFORMS = (
    'Microsoft Xbox',
    'Microsoft Xbox 360',
    'Microsoft Xbox One',
    'Sony Playstation 3',
    'Sony Playstation 4',
    'Sony Playstation Vita',
    'Android',
    'iOS',
    'Nintendo 3DS',
    'N-Gage',
    'Mac OS',
)

PLATFORM_MAP = {
    '3DO': '3do',
    'Arcade': 'arcade',
    'Amiga': 'amiga',
    'Apple II': 'apple-e',
    'Atari 2600': 'atari-2600',
    'Atari 5200': 'atari-5200',
    'Atari ST': 'atari-st',
    'Colecovision': 'colecovision',
    'PC': 'windows',
    'Sega Genesis': 'sega-genesis',
    'Sega Mega Drive': 'sega-genesis',
    'Sega 32X': 'sega-32x',
    'Sega Master System': 'sega-master-system',
    'Sega Saturn': 'sega-saturn',
    'Sega Game Gear': 'sega-game-gear',
    'Sega Dreamcast': 'sega-dreamcast',
    'Atari Jaguar': 'atari-jaguar',
    'Sony Playstation': 'sony-playstation',
    'Sony Playstation 2': 'sony-playstation-2',
    'Sony PSP': 'sony-psp',
    'Sony Playstation Portable': 'sony-psp',
    'Nintendo Entertainment System (NES)': 'nes',
    'Super Nintendo (SNES)': 'super-nintendo',
    'Neo Geo': 'neo-geo',
    'Neo Geo CD': 'neo-geo-cd',
    'Nintendo Game Boy': 'game-boy',
    'Nintendo Game Boy Color': 'nintendo-game-boy-color',
    'Nintendo Game Boy Advance': 'nintendo-game-boy-advance',
    'Nintendo 64': 'nintendo-64',
    'Nintendo GameCube': 'gamecube',
    'Nintendo DS': 'nintendo-ds',
    'Nintendo Wii': 'nintendo-wii',
    'Nintendo Wii U': 'nintendo-wii-u',
    'NeoGeo': 'neo-geo',
    'TurboGrafx 16': 'turbografx-16',
    'Vectrex': 'vectrex',
    'Sinclair ZX Spectrum': 'zx-spectrum',
}


def download_image(media_type, url):
    """Download an image from TheGamesDB (is necessary) and return its local path"""
    media_type_map = {
        'clearlogo': settings.TGD_CLEAR_LOGO_PATH,
        'banner': settings.TGD_BANNER_PATH,
        'screenshot': settings.TGD_SCREENSHOT_PATH,
        'fanart': settings.TGD_FANART_PATH
    }
    dest_path = os.path.join(media_type_map[media_type], os.path.basename(url))
    if not os.path.exists(dest_path):
        response = requests.get(url)
        with open(dest_path, 'w') as dest_file:
            dest_file.write(response.content)
    return dest_path


def convert_clearlogo_to_banner(logo_path):
    base_width, base_height = settings.BANNER_SIZE.split('x')
    base_ratio = float(base_width) / float(base_height)

    try:
        logo = Image.open(logo_path)
    except IOError:
        return
    logo_width = float(logo.width)
    logo_height = float(logo.height)
    logo_ratio = logo_width / logo_height

    margin_factor = 0.1
    if logo_ratio < base_ratio:
        new_h = logo_height + (logo_height * margin_factor)
        new_w = new_h * base_ratio
    else:
        new_w = logo_width + (logo_width * margin_factor)
        new_h = new_w / base_ratio

    new_image = Image.new('RGBA', (int(new_w), int(new_h)), (0, 0, 0, 255))
    if logo.mode == 'RGBA':
        mask = logo
    else:
        mask = None
    offset = (int((new_w - logo_width) / 2), int((new_h - logo_height) / 2))
    new_image.paste(logo, offset, mask)
    dest_path = os.path.join(settings.TGD_LUTRIS_BANNER_PATH,
                             os.path.basename(logo_path))
    new_image.save(dest_path)
    return dest_path


def api_request(url):
    response = requests.get(API_URL + url)
    return BeautifulSoup(response.content, 'xml')


def get_value(soup, field):
    if not soup:
        LOGGER.warn("No soup provided")
        return
    tag = soup.find(field)
    if tag:
        return tag.text


def get_similar(game_data):
    if not game_data:
        return
    similar = game_data.find('Similar')
    if similar:
        return [
            {
                'id': get_value(game, 'id'),
                'platform_id': get_value(game, 'PlatformId')
            } for game in similar.find_all('Game')
        ]


def get_pics(game_data, tag_name):
    results = []
    if not game_data:
        return results
    fanarts = game_data.find_all(tag_name)
    for fanart in fanarts:
        original = fanart.find('original')
        original_meta = original.attrs
        original_meta['url'] = original.get_text()
        results.append({
            'original': original_meta,
            'thumb': get_value(fanart, 'thumb'),
        })
    return results


def get_tags_with_attrs(soup, tag_name, value_name='value'):
    tags = soup.find_all(tag_name)
    results = []
    for tag in tags:
        attrs = tag.attrs
        if attrs:
            attrs[value_name] = tag.get_text()
        else:
            attrs = tag.get_text()
        results.append(attrs)
    if len(results) == 1:
        return results[0]
    else:
        return results


def get_games_list(query, remove_unsupported=True):
    soup = api_request('GetGamesList.php?name=' + query)
    game_list = []
    games = soup.find_all('Game')
    for game in games:
        platform = get_value(game, 'Platform')
        if remove_unsupported and platform in UNSUPPORTED_PLATFORMS:
            continue
        game_list.append({
            'id': get_value(game, 'id'),
            'game_title': get_value(game, 'GameTitle'),
            'release_date': get_value(game, 'ReleaseDate'),
            'platform': get_value(game, 'Platform')
        })
    return game_list


def get_game(game_id):
    soup = api_request('GetGame.php?id={}'.format(game_id))
    game_data = soup.find('Game')
    game_info = {
        'id': get_value(game_data, 'id'),
        'base_img_url': get_value(soup, 'baseImgUrl'),
        'game_title': get_value(game_data, 'GameTitle'),
        'platform': get_value(game_data, 'Platform'),
        'release_date': get_value(game_data, 'ReleaseDate'),
        'overview': get_value(game_data, 'Overview'),
        'esrb': get_value(game_data, 'ESRB'),
        'publisher': get_value(game_data, 'Publisher'),
        'developer': get_value(game_data, 'Developer'),
        'rating': get_value(game_data, 'Rating'),
        'similar': get_similar(game_data),
        'fanarts': get_pics(game_data, 'fanart'),
        'boxarts': get_tags_with_attrs(game_data, 'boxart'),
        'banners': get_tags_with_attrs(game_data, 'banner'),
        'screenshots': get_pics(game_data, 'screenshot'),
        'clearlogo': get_tags_with_attrs(game_data, 'clearlogo'),
    }
    return game_info


def get_lutris_platform(platform_name):
    try:
        slug = PLATFORM_MAP[platform_name]
    except KeyError:
        LOGGER.error('No map for %s', platform_name)
        return
    return Platform.objects.get(slug=slug)


def to_lutris(game):
    lutris_game = {}
    lutris_game['name'] = game['game_title']
    if game['release_date']:
        match = re.search(r'\d{4}', game['release_date'])
        lutris_game['year'] = match.group(0)

    publisher = get_or_create_company(game['publisher'])
    if publisher:
        lutris_game['publisher'] = publisher.id

    if game['developer'] == game['publisher']:
        developer = publisher
    else:
        developer = get_or_create_company(game['developer'])
    if developer:
        lutris_game['developer'] = developer.id

    platform = get_lutris_platform(game['platform'])
    if platform:
        lutris_game['platforms'] = [platform.id]
    if game['clearlogo']:
        clearlogo_url = game['base_img_url'] + game['clearlogo']['value']
        logo_path = download_image('clearlogo', clearlogo_url)
        banner_path = convert_clearlogo_to_banner(logo_path)
        if banner_path:
            banner_url = banner_path[len(settings.MEDIA_ROOT):].strip('/')
            lutris_game['banner'] = settings.MEDIA_URL + banner_url
    return lutris_game


def get_or_create_company(name):
    if not name:
        return
    slug = slugify(name)[:50]
    try:
        company = Company.objects.get(slug=slug)
    except Company.DoesNotExist:
        company = Company.objects.create(
            slug=slug,
            name=name
        )
    return company
