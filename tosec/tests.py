import os
from django.test import TestCase
from .parser import TosecParser, smart_split


class TestTosecParser(TestCase):
    def setUp(self):
        self.filename = 'Apple 1 - Games (TOSEC-v2011-08-31_CM).dat'
        base_path = os.path.dirname(os.path.abspath(__file__))
        dat_path = os.path.join(base_path, 'fixtures', self.filename)
        with open(dat_path, 'r') as dat_file:
            self.dat_content = dat_file.readlines()

    def test_dat_file_is_loaded(self):
        self.assertGreater(len(self.dat_content), 25)
        self.assertEqual(self.dat_content[6], ')\r\n')

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
