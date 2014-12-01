import re
from . import constants


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
            elif string[i - len(end_sep) + 1:i + 1] == end_sep and in_word:
                in_word = False
        char = string[i]
        if char in (' ', '\t') and not in_word:
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
    tosec_re = (
        r'(?P<title>.*?) '
        r'(?:\((?P<demo>demo(?:-[a-z]{5,9})*)\) )*'
        r'\((?P<date>[0-9x]{4}(?:-[0-9]{2}(?:-[0-9x]{2})*)*)\)'
        r'\((?P<publisher>.*?)\)'
    )
    flags_re = r'\((.*?)\)*'

    parts = [
        'title',
        'version',
        'demo',
        'date',
        'publisher',
        'system',
        'video',
        'country',
        'language',
        'copyright',
        'development',
        'media',
        'dump',
        'cracked',
        'fixed',
        'hacked',
        'modified',
        'pirated',
        'trained',
        'translated',
        'over_dump',
        'under_dump',
        'virus',
        'bad_dump',
        'alternate',
        'known_verified',
    ]

    empty = {
        'title': None,
        'demo': None,
        'date': None,
        'publisher': None
    }

    def __init__(self, name):
        print self.tosec_re
        self.filename = name
        self.matches = re.search(self.tosec_re, name)
        groupdict = self.matches.groupdict() if self.matches else self.empty
        self.title = groupdict['title']
        self.demo = groupdict['demo']
        self.date = groupdict['date']
        self.publisher = groupdict['publisher']

        if self.matches:
            remainder = self.filename[self.matches.end():]
            self.flags = [s for s in re.split(r'(\(.*?\))', remainder) if s]
            self.set_flags()

    def set_flags(self):
        current_flag_index = self.parts.index('publisher') + 1
        for flag in self.flags:
            if not flag.startswith('('):
                return
            flag_value = flag.strip('()')
            flag_type = self.parts[current_flag_index]
            flag_method = getattr(self, 'set_' + flag_type)
            flag_set = False
            last_index = self.parts.index('cracked')
            while current_flag_index < last_index and not flag_set:
                flag_set = flag_method(flag_value)
                current_flag_index += 1

    def set_system(self, value):
        """This field is reserved for collections that require multiple system
        support, such as Amiga, which could require (A500), (A1000) etc., to
        address compatibility issues.
        """
        self.system = None
        if value in constants.SYSTEMS_FLAGS:
            self.system = value
            return True

    def set_video(self, value):
        """The video field is only used in cases where the images cannot be
        classified by countries or languages, but for example only the PAL or
        NTSC video formats they were released in.
        """
        self.video = None
        if value in constants.VIDEO_FLAGS:
            self.video = value
            return True

    def set_country(self, value):
        """This field is used to classify the country of origin. The codes used
        are defined by the international ISO 3166-1 alpha-2 standard.
        In the case of two countries being required, both are given,
        alphabetised and separated by a hyphen:

        For example: (DE-GB) - Released in Germany and the United Kingdom

        For example: (DE-FR) - Released in France and Germany

        For example: (EU-US) - Released in Europe and the US
        """
        self.country = None
        countries = value.split('-')
        if all([c in constants.COUNTRY_FLAGS for c in countries]):
            self.country = value
            return True

    def set_language(self, value):
        """The language used in the software. The codes used are defined by the
        international ISO 639-1 standard.

        Language flags usage has to obey a few basic rules for reasons of
        enforced simplicity:

        English is seen as the default language, in other words when no
        language or country flag is used it is taken that the software is in
        English.

        On the other hand if a country flag is used, we assume that the
        software language is the official country language, so there is no need
        to use "(JP)(ja) ", "(DE)(de)" or "(PT)(pt)" only the country code.
        Conversely, software released in Japan but using English language
        should be "(JP)(en)" for example.

        When two languages are used they should be alphabetically ordered,
        unless if one is in English then it always comes first, e.g. (en-de).

        In cases of more than two languages or countries being required, (Mx)
        is used to represent multiple languages, where x is the number of
        languages:
        """
        self.language = None
        languages = value.split('-')
        if all([l in constants.LANGUAGE_FLAGS for l in languages]):
            self.language = value
            return True
        if re.match(r'^M\d$', value):
            self.language = value
            return True

    def set_copyright(self, value):
        """This field is used to denote the copyright status of software if
        applicable. If the software has been realised to the Public Domain by
        the copyright holder or if it is Freeware or Shareware for example,
        this is the place to note it.

        If a Shareware title is registered, -R is appended to the field. This
        can also be used for Cardware and Giftware titles.
        """
        self.copyright = None
        if value in constants.COPYRIGHT_FLAGS:
            self.copyright = value
            return True
