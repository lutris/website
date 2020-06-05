"""URL converters"""


class VersionConverter:
    """URL converter to match version numbers"""
    regex = r'[\w\-\.\_]+'

    @staticmethod
    def to_python(value):
        """Dispatch the value in the URL to the python code"""
        return str(value)

    @staticmethod
    def to_url(value):
        """Convert the python value to a suitable value for URLs"""
        return value
