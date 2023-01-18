"""TOSEC naming convention parser"""
import re
import logging
from tosec import constants

LOGGER = logging.getLogger(__name__)

class TosecNamingConvention:  # pylint: disable=too-many-instance-attributes
    """Naming conventions used in TOSEC files"""
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
        'media_label',
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
        for part in self.parts:
            setattr(self, part, None)
        self.media_numbers = []
        self.media_total = None
        self.filename = name
        self.matches = re.search(self.tosec_re, name)
        groupdict = self.matches.groupdict() if self.matches else self.empty
        self.title = groupdict['title']
        self.demo = groupdict['demo']
        self.date = groupdict['date']
        self.publisher = groupdict['publisher']

        self.system = ""
        self.video = ""
        self.country = ""
        self.language = ""
        self.copyright = ""
        self.development = ""
        self.media = ""
        self.media_additional = ""
        self.media_label = ""

        if self.matches:
            remainder = self.filename[self.matches.end():]
            flag_match = re.search(r'\(.*\)', remainder)
            if flag_match:
                flag_part = remainder[flag_match.start():flag_match.end()]
                flags = [s for s in re.split(r'(\(.*?\))', flag_part) if s]
                self.set_flags(flags)
                remainder = remainder[flag_match.end():]

            dump_match = re.search(r'\[.*\]', remainder)
            if dump_match:
                dump_part = remainder[dump_match.start(), dump_match.end()]
                dump_flags = [d for d in re.split(r'(\[.*?\])', dump_part) if d]
                self.set_dump_flags(dump_flags)

    def set_flags(self, flags):
        """Dispatch flag assignment to the class' set_* methods"""
        current_flag_index = self.parts.index('publisher') + 1
        for flag in flags:
            # if not flag.startswith('('):
            #     return
            flag_value = flag.strip('()')
            flag_set = False
            last_index = self.parts.index('cracked')
            while current_flag_index < last_index and not flag_set:
                flag_type = self.parts[current_flag_index]
                flag_method = getattr(self, 'set_' + flag_type)
                flag_set = flag_method(flag_value)
                current_flag_index += 1

    def set_dump_flags(self, dump_flags):
        """Set attributes on the instance from the game's dump flags"""
        dump_flags_attrs = {
            'cr': 'cracked',
            'f': 'fixed',
            'h': 'hacked',
            'm': 'modified',
            'p': 'pirated',
            't': 'trained',
            'tr': 'translated',
            'o': 'over_dump',
            'u': 'under_dump',
            'v': 'virus',
            'b': 'bad_dump',
            'a': 'alternate',
            '!': 'known_verified',
        }
        for flag in dump_flags:
            flag_parts = flag.split()
            flag_name = flag_parts[0]
            if flag_name in dump_flags_attrs:
                if len(flag_parts) == 1:
                    value = True
                else:
                    value = ' '.join(flag_parts[1:])
                setattr(self, dump_flags_attrs[flag_name], value)

    def set_system(self, value):
        """This field is reserved for collections that require multiple system
        support, such as Amiga, which could require (A500), (A1000) etc., to
        address compatibility issues.
        """
        if value in constants.SYSTEMS_FLAGS:
            self.system = value
            return True

    def set_video(self, value):
        """The video field is only used in cases where the images cannot be
        classified by countries or languages, but for example only the PAL or
        NTSC video formats they were released in.
        """
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
        if value in constants.COPYRIGHT_FLAGS:
            self.copyright = value
            return True

    def set_development(self, value):
        """This field is for marking alpha, beta, preview, prototype or
        pre-release versions of software titles.
        """
        if value in constants.DEVELOPMENT_FLAGS:
            self.development = value
            return True

    def set_media(self, value):
        """This field is used if the software spans more than one
        CD/DVD/GD-ROM, diskette, tape or file. Note that apart from the normal
        possibilities (Disk, Disc, Tape …), "Side x of y" is also allowed.

        For example, where there are 9 or less disks, the format of "(Disk x of
        y)" is used, if there are 10 or more disks then (Disk xx of yy) should
        be used, there can also be the case where more than one volume is
        grouped in a single image, so something like (Part 1-2 of 3) is also
        allowed.
        """
        media_info = value.split()
        if media_info[0] in constants.MEDIA_FLAGS:
            self.media = media_info[0]
            self.media_numbers = media_info[1].split('-')
            if len(media_info) > 2:
                if media_info[2] != 'of':
                    LOGGER.warning('Invalid value for media in %s',
                                   self.filename)
                self.media_total = media_info[3]
            if len(media_info) > 4:
                self.media_additional = ' '.join(media_info[4:])
            return True

    def set_media_label(self, value):
        """If the disk label is required, this field should contain it. This
        field is always the last flag using ( ) brackets, just before any
        existent [ ] flags.

        This is mainly used when a "Save Disk", "Program Disk", "Scenery Disk"
        etc.  might be requested by the software when running. For example
        (Disk 2 of 2) is not useful by itself when the program asks you to
        "Insert Character Disk".
        """
        self.media_label = value
