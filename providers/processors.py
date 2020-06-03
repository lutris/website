"""Transforms data from third party services to Lutris compatible data"""


def clean_name(name):
    """Clean up a game name"""
    extras = (
        "tech demo",
        "demo",
        "demo 2",
        "gold pack",
        "complete pack",
        "the final cut",
        "enhanced edition",
        "free preview",
        "complete edition",
        "alpha version",
        "pc edition",
        "ultimate edition",
        "platinum edition",
        "commander pack",
        "gold edition",
        "drm free edition",
        "drm-free",
        "directx 11 version",
        "remake",
        "original game soundtrack",
        "soundtrack",
        "cd version",
        "deluxe edition",
        "galaxy edition",
        "collector's edition",
        "humble deluxe edition",
        "gog edition",
        "pre-order",
        "game of the year",
        "+ all dlc",
        "base game",
    )
    for extra in extras:
        if name.strip(")").lower().endswith(extra):
            name = name[:-len(extra)].strip(" -:®™(").replace("™", "")
    return name
