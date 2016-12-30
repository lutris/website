SUCCESS = (True, "")


class ScriptValidator(object):
    def __init__(self, script):
        self.rules = [
            doesnt_contain_useless_fields,
            files_is_an_array,
            scummvm_has_gameid,
        ]
        self.script = script
        self.errors = []
        self.valid = True

    def is_valid(self):
        for rule in self.rules:
            success, message = rule(self.script)
            if not success:
                self.errors.append(message)
                self.valid = False
        return self.valid


def doesnt_contain_useless_fields(script):
    for field in (
        'version', 'gogid', 'humbleid', 'game_slug', 'description',
        'installer_slug', 'name', 'notes', 'runner', 'slug', 'steamid', 'year'
    ):
        if field in script:
            return (False, "Don't put a '{}' field in the script.".format(field))
    return SUCCESS


def files_is_an_array(script):
    if 'files' in script:
        if not isinstance(script['files'], list):
            return (False, "'files' section should be an array.")
    return SUCCESS


def scummvm_has_gameid(script):
    runner = script.get('runner')
    if runner != 'scummvm':
        return SUCCESS
    if 'game' not in script:
        return (
            False,
            "Missing section 'game'"
        )
    if 'game_id' not in script['game']:
        return (
            False,
            "ScummVM game should have a game identifier in the 'game' section"
        )
    return SUCCESS
