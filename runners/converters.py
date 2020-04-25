class VersionConverter:
    regex = '[\w\-\.\_]+'

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return value
