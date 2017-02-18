import yaml
from runners.models import Runner
from games.models import DEFAULT_INSTALLER
SUCCESS = (True, "")


def get_installer_script(installer):
    script = yaml.safe_load(installer.content)
    if not script:
        return {}
    return script


def validate_installer(installer):
    errors = []
    is_valid = True
    rules = [
        script_is_not_the_default_one,
        doesnt_contain_useless_fields,
        files_is_an_array,
        scummvm_has_gameid,
    ]
    for rule in rules:
        success, message = rule(installer)
        if not success:
            errors.append(message)
            is_valid = False

    return (is_valid, errors)


def script_is_not_the_default_one(installer):
    script = get_installer_script(installer)
    if script == DEFAULT_INSTALLER:
        return (
            False,
            "Really? You haven't even modified the default installer"
        )
    return SUCCESS


def doesnt_contain_useless_fields(installer):
    script = get_installer_script(installer)
    for field in (
        'version', 'gogid', 'humbleid', 'game_slug', 'description',
        'installer_slug', 'name', 'notes', 'runner', 'slug', 'steamid', 'year'
    ):
        if field in script:
            return (False, "Don't put a '{}' field in the script.".format(field))
    return SUCCESS


def files_is_an_array(installer):
    script = get_installer_script(installer)
    if 'files' in script:
        if not isinstance(script['files'], list):
            return (False, "'files' section should be an array.")
    return SUCCESS


def scummvm_has_gameid(installer):
    try:
        runner = installer.runner.name
    except Runner.DoesNotExist:
        runner = ""
    script = get_installer_script(installer)
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
