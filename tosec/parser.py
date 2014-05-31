import re
from . import constants


def is_separator(char):
    return char == ' ' or char == '\t'


def smart_split(string, sep=None):
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
    for i in range(len(string)):
        if sep:
            if string[i:i + len(sep)] == sep and not in_word:
                in_word = True
            elif string[i - len(sep) + 1:i + 1] == end_sep and in_word:
                in_word = False
        char = string[i]
        if is_separator(char) and not in_word:
            if word:
                splits.append(word)
                word = ''
        else:
            word += char
    if word:
        splits.append(word)
    return splits


class TosecParser(object):
    def __init__(self, contents):
        """contents is an list containing the lines of a Tosec dat file"""
        self.contents = contents
        self.headers = {}
        self.games = []

    def _iter_contents(self):
        """Iterate over the dat's contents"""
        for line in self.contents:
            yield line

    @staticmethod
    def parse_line(line):
        key, raw_value = line.split(' ', 1)
        return key, raw_value.strip("\"")

    def extract_rom(self, line):
        line = line[1:-1]  # Strip parenthesis
        parts = smart_split(line, sep='"')
        game_dict = {}
        for i in range(0, len(parts) - 1, 2):
            key = parts[i]
            value = parts[i + 1].strip('"')
            game_dict[key] = value
        return game_dict

    def extract_line(self, line, item):
        if line == ')':
            return True
        else:
            parts = self.parse_line(line)
            if parts[1] == '(':
                return
            if parts[0] == 'rom':
                # FIXME there can be multiple roms in one entry
                item['rom'] = self.extract_rom(parts[1])
            else:
                item[parts[0]] = parts[1]

    def parse(self):
        headers_ok = False
        game = {}
        for line in self._iter_contents():
            line = line.strip()
            if not line:
                continue
            if not headers_ok:
                headers_ok = self.extract_line(line, self.headers)
            else:
                game_ok = self.extract_line(line, game)
                if game_ok:
                    self.games.append(game)
                    game = {}


class TosecNamingConvention(object):
    systems = [s.replace('+', '\+') for s in constants.SYSTEMS_FLAGS]
    tosec_re = (
        r'(?P<title>.*?) '
        r'(?:\((?P<demo>demo(?:-[a-z]{5,9})*)\) )*'
        r'\((?P<date>[0-9x]{4}(?:-[0-9]{2}(?:-[0-9x]{2})*)*)\)'
        r'\((?P<publisher>.*?)\)'
        r'(?:\((?P<system>%s)\))*' % '|'.join(systems)
    )


    def __init__(self, name):
        print self.tosec_re
        self.matches = re.search(self.tosec_re, name)

    def __getattr__(self, name):
        if not self.matches:
            return
        try:
            return self.matches.group(name)
        except IndexError:
            pass
