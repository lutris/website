"""Utilities for handling TOSEC files"""
from tosec import models
from tosec.parsers.xml import TosecParser



def smart_split(string, sep=None):
    """Split a string while preserving separator groups"""
    sep_map = {
        '(': ')',
        '( ': ' )',
        '<': '/>',
        '{': '}',
        '[': ']',
    }
    splits = []
    word = ''
    in_word = False
    end_sep = sep_map.get(sep, sep)
    for i, char in enumerate(string):
        if sep:
            if string[i:i + len(sep)] == sep and not in_word:
                in_word = True
            elif string[i - len(end_sep) + 1:i + 1] == end_sep and in_word:
                in_word = False
        if char in (' ', '\t') and not in_word:
            if word:
                splits.append(word)
                word = ''
        else:
            word += char
    if word:
        splits.append(word)
    return splits



def import_tosec_database(filename):
    """Import a TOSEC database referenced by filename"""
    tosec_parser = TosecParser(filename)
    tosec_parser.parse()

    category = models.TosecCategory(
        name=tosec_parser.headers['name'],
        description=tosec_parser.headers['description'],
        category=tosec_parser.headers['category'],
        version=tosec_parser.headers['version'],
        author=tosec_parser.headers['author'],
    )
    category.save()

    for game in tosec_parser.games:
        game_row = models.TosecGame(
            category=category,
            name=game['name'],
            description=game['description'],
        )
        game_row.save()
        for rom in game["roms"]:
            rom_row = models.TosecRom(
                game=game_row,
                name=rom['name'],
                size=rom['size'],
                crc=rom['crc'],
                md5=rom.get('md5', ''),
                sha1=rom.get('sha1', ''),
            )
            rom_row.save()
