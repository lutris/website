SUCCESS = (True, "")


class ScriptValidator(object):
    def __init__(self, script):
        self.rules = [
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


def files_is_an_array(script):
    if 'files' in script:
        if not isinstance(script['files'], list):
            return (False, "'files' section should be an array.")
    return SUCCESS


class scummvm_has_gameid(object):
    def is_valid(self, script):
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
