import urllib2


def get_capsule(steamid):
    steam_cdn = "http://cdn2.steampowered.com"
    capsule_url = steam_cdn + "/v/gfx/apps/%d/capsule_184x69.jpg"
    return urllib2.urlopen(capsule_url % steamid).read()
