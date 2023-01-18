"""Utilities for handling TOSEC files"""
from tosec import models
from tosec.parser import TosecParser


def import_tosec_database(filename):
    """Import a TOSEC database referenced by filename"""
    with open(filename, 'r') as tosec_dat:
        dat_contents = tosec_dat.readlines()

    tosec_parser = TosecParser(dat_contents)
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
        rom = game['rom']
        rom_row = models.TosecRom(
            game=game_row,
            name=rom['name'],
            size=rom['size'],
            crc=rom['crc'],
            md5=rom.get('md5', ''),
            sha1=rom.get('sha1', ''),
        )
        rom_row.save()
