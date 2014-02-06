class TosecParser(object):
    def __init__(self, contents):
        self.contents = contents
        self.headers = {}
        self.games = []

    def _iter_contents(self):
        for line in self.contents:
            yield line

    @staticmethod
    def parse_line(line):
        key, raw_value = line.split(' ', 1)
        return key, raw_value.strip("\"")

    def extract_line(self, line, item):
        if line == ')':
            return True
        else:
            parts = self.parse_line(line)
            if parts[1] == '(':
                return
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
