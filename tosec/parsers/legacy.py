from tosec.utils import smart_split


class TosecOldParser:
    """Parser for TOSEC dat files"""
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
        """Parse a single line of data"""
        try:
            key, raw_value = line.split(' ', 1)
        except ValueError:
            raise ValueError("Invalid line %s" % line)
        return key, raw_value.strip("\"")

    @staticmethod
    def extract_rom(line):
        """Extract ROM information from a line"""
        line = line[1:-1]  # Strip parenthesis
        parts = smart_split(line, sep='"')
        game_dict = {}
        for i in range(0, len(parts) - 1, 2):
            key = parts[i]
            value = parts[i + 1].strip('"')
            game_dict[key] = value
        return game_dict

    def extract_line(self, line, item):
        """This seems incomplete..."""
        if line == ')':
            return True
        parts = self.parse_line(line)
        if parts[1] == '(':
            return
        if parts[0] == 'rom':
            # FIXME there can be multiple roms in one entry
            item['rom'] = self.extract_rom(parts[1])
        else:
            item[parts[0]] = parts[1]

    def parse(self):
        """Parse the dat file"""
        headers_ok = False
        game = {}
        for line in self._iter_contents():
            line = line.strip()
            if not line:
                continue
            if headers_ok:
                game_ok = self.extract_line(line, game)
                if game_ok:
                    self.games.append(game)
                    game = {}
            else:
                headers_ok = self.extract_line(line, self.headers)
