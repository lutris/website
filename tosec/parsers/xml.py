"""XML parser"""
import xml.etree.ElementTree


class TosecParser:
    """Parser for XML based dat files"""
    def __init__(self, filename):
        self.headers = {}
        self.games = []
        self.root = xml.etree.ElementTree.parse(filename).getroot()

    def parse(self):
        """Parse the XML file"""
        header = self.root.find("header")
        for header_tag in header:
            self.headers[header_tag.tag] = header_tag.text
        for game_tag in self.root.findall("game"):
            game = {
                "name": game_tag.attrib["name"],
                "roms": []
            }
            description = game_tag.find("description")
            game["description"] = description.text
            for rom_tag in game_tag.findall("rom"):
                game["roms"].append(rom_tag.attrib)
            self.games.append(game)
