# pylint: disable=missing-docstring,invalid-name
import os
from django.test import TestCase
from .parser import TosecParser, TosecNamingConvention, smart_split


class TestTosecParser(TestCase):
    def setUp(self):
        self.filename = 'Apple 1 - Games (TOSEC-v2011-08-31_CM).dat'
        base_path = os.path.dirname(os.path.abspath(__file__))
        dat_path = os.path.join(base_path, 'fixtures', self.filename)
        with open(dat_path, 'r') as dat_file:
            self.dat_content = dat_file.readlines()

    def test_dat_file_is_loaded(self):
        self.assertGreater(len(self.dat_content), 25)
        self.assertEqual(self.dat_content[6], ')\n')

    def test_can_parse_headers(self):
        parser = TosecParser(self.dat_content)
        parser.parse()
        self.assertEqual(parser.headers['name'], parser.headers['category'])

    def test_can_parse_games(self):
        parser = TosecParser(self.dat_content)
        parser.parse()
        self.assertEqual(len(parser.games), 3)
        self.assertIn('Blackjack', parser.games[0]['name'])


class TestSplitter(TestCase):
    def test_can_normally_split_strings(self):
        string = "aaa bbb   ccc      ddd\t\teee"
        expected = ['aaa', 'bbb', 'ccc', 'ddd', 'eee']
        self.assertEqual(smart_split(string), expected)

    def test_can_split_with_special_delimiter(self):
        string = "name \"aaa bbb ccc\" id 1"
        expected = ['name', '"aaa bbb ccc"', 'id', '1']
        self.assertEqual(smart_split(string, sep='"'), expected)

    def test_can_split_with_dual_separator(self):
        string = "rom (bli blu) foo bar"
        expected = ['rom', '(bli blu)', 'foo', 'bar']
        self.assertEqual(smart_split(string, sep="("), expected)

    def test_can_split_multiple_chars(self):
        string = 'rom ( name "Atlantis (1983)(Imagic)(EU-US).bin" size 4096 )'
        expected = [
            'rom',
            '( name "Atlantis (1983)(Imagic)(EU-US).bin" size 4096 )'
        ]
        self.assertEqual(smart_split(string, sep='( '), expected)


class TestNamingConvention(TestCase):

    def test_can_parse_demo(self):
        name = "Legend of TOSEC, The (demo-playable) (1986)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.demo, 'demo-playable')

        name = "Legend of TOSEC, The (demo) (1986)(Devstudio)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.demo, 'demo')

    def test_can_parse_date(self):
        name = "Legend of TOSEC, The (19xx)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.date, '19xx')

        name = "Legend of TOSEC, The (200x)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.date, '200x')

        name = "Legend of TOSEC, The (1986)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.date, '1986')

        name = "Legend of TOSEC, The (199x)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.date, '199x')

        name = "Legend of TOSEC, The (2001-01)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.date, '2001-01')

        name = "Legend of TOSEC, The (1986-06-21)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.date, '1986-06-21')

        name = "Legend of TOSEC, The (19xx-12)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.date, '19xx-12')

        name = "Legend of TOSEC, The (19xx-12-25)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.date, '19xx-12-25')

        name = "Legend of TOSEC, The (19xx-12-2x)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.date, '19xx-12-2x')

        name = "Legend of TOSEC, The (19xx-12-2abc)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertFalse(tosec_name.date)

        name = "Legend of TOSEC, The (99)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertFalse(tosec_name.date)

    def test_can_get_title(self):
        name = "Legend of TOSEC, The (199x)(-)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.title, "Legend of TOSEC, The")

    def test_can_get_publisher(self):
        name = "Legend of TOSEC, The (1986)(Devstudio)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.publisher, 'Devstudio')

    def test_can_get_system(self):
        name = "Legend of TOSEC, The (1986)(Devstudio)(+ 2)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.system, '+ 2')

        name = "Legend of TOSEC, The (1986)(Devstudio)(A4000)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.system, 'A4000')

    def test_can_get_video(self):
        name = "Legend of TOSEC, The (1986)(Devstudio)(PAL)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.video, 'PAL')

        name = "Legend of TOSEC, The (1986)(Devstudio)(NTSC)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.video, 'NTSC')

    def test_can_get_country(self):
        name = "Legend of TOSEC, The (1986)(Devstudio)(US)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.country, 'US')

        name = "Legend of TOSEC, The (1986)(Devstudio)(JP)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.country, 'JP')

        name = "Legend of TOSEC, The (1986)(Devstudio)(DE)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.country, 'DE')

        name = "Legend of TOSEC, The (1986)(Devstudio)(DE-FR)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.country, 'DE-FR')

    def test_can_get_language(self):
        name = "Legend of TOSEC, The (1986)(Devstudio)(pt)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.language, 'pt')

        name = "Legend of TOSEC, The (1986)(Devstudio)(JP)(en)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.country, 'JP')
        self.assertEqual(tosec_name.language, 'en')

        name = "Legend of TOSEC, The (1986)(Devstudio)(M3)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.language, 'M3')

        name = "Legend of TOSEC, The (1986)(Devstudio)(M4)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.language, 'M4')

        name = "Legend of TOSEC, The (1986)(Devstudio)(de-fr)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.language, 'de-fr')

    def test_can_get_copyright(self):
        name = "Legend of TOSEC, The (1986)(Devstudio)(PD)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.copyright, 'PD')

        name = "Legend of TOSEC, The (1986)(Devstudio)(FR)(SW)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.country, 'FR')
        self.assertEqual(tosec_name.copyright, 'SW')

    def test_can_test_development(self):
        name = "Legend of TOSEC, The (1986)(Devstudio)(beta)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.development, 'beta')

        name = "Legend of TOSEC, The (1986)(Devstudio)(proto)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.development, 'proto')

    def test_can_get_media(self):
        name = "Legend of TOSEC, The (1986)(Devstudio)(US)(File 1 of 2)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.media, 'File')
        self.assertEqual(tosec_name.media_numbers, ['1'])
        self.assertEqual(tosec_name.media_total, '2')

        name = "Legend of TOSEC, The (1986)(Devstudio)(US)(Disc 1 of 6)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.media, 'Disc')
        self.assertEqual(tosec_name.media_numbers, ['1'])
        self.assertEqual(tosec_name.media_total, '6')

        name = "Legend of TOSEC, The (1986)(Devstudio)(US)(Disk 06 of 13)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.media, 'Disk')
        self.assertEqual(tosec_name.media_numbers, ['06'])
        self.assertEqual(tosec_name.media_total, '13')

        name = "Legend of TOSEC, The (1986)(Devstudio)(US)(Side A)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.media, 'Side')
        self.assertEqual(tosec_name.media_numbers, ['A'])
        self.assertEqual(tosec_name.media_total, None)

        name = "Legend of TOSEC, The (1986)(Devstudio)(US)(Tape 2 of 2 Side B)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.media, 'Tape')
        self.assertEqual(tosec_name.media_numbers, ['2'])
        self.assertEqual(tosec_name.media_total, '2')
        self.assertEqual(tosec_name.media_additional, 'Side B')

        name = "Legend of TOSEC, The (1986)(Devstudio)(US)(Part 1-2 of 3)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.media, 'Part')
        self.assertEqual(tosec_name.media_numbers, ['1', '2'])
        self.assertEqual(tosec_name.media_total, '3')

    def test_media_label(self):
        name = "TOSEC, The (1986)(Devstudio)(US)(Disk 3 of 3)(Character Disk)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.media, 'Disk')
        self.assertEqual(tosec_name.media_total, '3')
        self.assertEqual(tosec_name.media_label, 'Character Disk')

        name = "TOSEC, The (1986)(Devstudio)(US)(Disk 1 of 2)(Program)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.media, 'Disk')
        self.assertEqual(tosec_name.media_total, '2')
        self.assertEqual(tosec_name.media_label, 'Program')

        name = "TOSEC, The (1986)(Devstudio)(US)(Disk 2 of 2)(Data)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.media, 'Disk')
        self.assertEqual(tosec_name.media_total, '2')
        self.assertEqual(tosec_name.media_label, 'Data')

        name = "TOSEC, The (1986)(Devstudio)(US)(Bonus Disc)"
        tosec_name = TosecNamingConvention(name)
        self.assertEqual(tosec_name.media_label, 'Bonus Disc')
