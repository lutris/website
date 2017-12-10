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
        installer_steps_have_one_key,
        scummvm_has_gameid,
        winesteam_scripts_use_correct_prefix,
        dont_disable_monitor,
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
        'version', 'gogslug', 'gogid', 'humbleid', 'game_slug', 'description',
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


def installer_steps_have_one_key(installer):
    script = get_installer_script(installer)
    if 'installer' in script:
        if not isinstance(script['installer'], list):
            return (False, "'installer' section should be an array.")
        for step in script['installer']:
            if isinstance(step, dict) and len(step.keys()) > 1:
                return (False, "Installer step %s shouldn't have more than one key (check your indentation)" % step)
    return SUCCESS


def scummvm_has_gameid(installer):
    try:
        runner = installer.runner.slug
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


def winesteam_scripts_use_correct_prefix(installer):
    try:
        runner = installer.runner.slug
    except Runner.DoesNotExist:
        runner = ""
    if runner != 'winesteam':
        return SUCCESS
    script = get_installer_script(installer)
    if 'game' not in script:
        return (
            False,
            "Missing section game"
        )
    if '$USER' in script['game'].get('prefix', ''):
        return (
            False,
            "Do not create the prefix in the home folder, use $GAMEDIR/prefix"
        )
    if script['game'].get('prefix', '').strip() == '$GAMEDIR':
        return (
            False,
            "Do not create the prefix directly in the game folder, use $GAMEDIR/prefix"
        )
    return SUCCESS


def dont_disable_monitor(installer):
    script = get_installer_script(installer)
    if 'system' not in script:
        return SUCCESS
    if 'disable_monitor' in script['system']:
        return (
            False,
            "Do not disable the process monitor in installers, if you have "
            "issues with the process monitor, submit an issue on Github"
        )
    return SUCCESS
