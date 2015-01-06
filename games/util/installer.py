class ScriptValidator(object):
    def __init__(self, script):
        self.rules = [
            FilesShouldBeArray(),
            ScummVMGameHasGameID(),
        ]
        self.script = script
        self.errors = []
        self.valid = True

    def is_valid(self):
        for rule in self.rules:
            if not rule.is_valid(self.script):
                self.errors.append(rule.message)
                self.valid = False
        return self.valid


class FilesShouldBeArray(object):
    def is_valid(self, script):
        if 'files' in script:
            if not isinstance(script['files'], list):
                self.message = "'files' section should be an array."
                return False
        return True


class ScummVMGameHasGameID(object):
    def is_valid(self, script):
        runner = script.get('runner')
        if runner != 'scummvm':
            return True
        if 'game' not in script:
            self.message = ("Missing section 'game'")
            return False
        if 'game_id' not in script['game']:
            self.message = ("ScummVM game should have a "
                            "game identifier in the 'game' section")
            return False
        return True
