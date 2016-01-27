import requests
from bs4 import BeautifulSoup


API_URL = "http://thegamesdb.net/api/"


def api_request(url):
    response = requests.get(API_URL + url)
    return BeautifulSoup(response.content, 'xml')


def get_value(soup, field):
    tag = soup.find(field)
    if tag:
        return tag.text


def get_similar(game_data):
    similar = game_data.find('Similar')
    if similar:
        return [
            {
                'id': get_value(game, 'id'),
                'platform_id': get_value(game, 'PlatformId')
            } for game in similar.find_all('Game')
        ]


def get_pics(game_data, tag_name):
    fanarts = game_data.find_all(tag_name)
    results = []
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


def get_games_list(query):
    # soup = api_request('GetGamesList.php?name=' + query)
    content = open('/home/strider/GetGamesList.xml').read()
    soup = BeautifulSoup(content, 'xml')
    game_list = []
    games = soup.find_all('Game')
    for game in games:
        game_list.append({
            'id': get_value(game, 'id'),
            'game_title': get_value(game, 'GameTitle'),
            'release_date': get_value(game, 'ReleaseDate'),
            'platform': get_value(game, 'Platform')
        })
    return game_list


def get_game(game_id):
    # soup = api_request('GetGame.php?id={}'.format(game_id))
    content = open("/home/strider/crysis.xml").read()
    soup = BeautifulSoup(content, 'xml')
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
