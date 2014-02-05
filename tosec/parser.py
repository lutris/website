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

    def parse(self):
        headers_ok = False
        for line in self._iter_contents():
            line = line.strip()
            if not headers_ok:
                if line == ')':
                    headers_ok = True
                else:
                    header_item = self.parse_line(line)
                    if header_item[1] == '(':
                        continue
                    self.headers[header_item[0]] = header_item[1]
