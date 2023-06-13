# pylint:disable=no-member
"""Celery tasks for account related jobs"""
from collections import defaultdict
from celery.utils.log import get_task_logger
from django.db.models import Q

from common.util import load_yaml, dump_yaml
from common.models import KeyValueStore
from games import models

from lutrisweb.celery import app
LOGGER = get_task_logger(__name__)


OBSOLETE_RUNNERS = (
    "winesteam",
    "browser"
)

# Fixes typos and non existent Winetricks verbs.
# Empty string means the task will be removed
WINETRICKS_FIXES = {
    '--force': "",
    '--unattended': "",
    '-f': "",
    'adobeair': "",
    "corfonts": "corefonts",
    'ariel': "arial",
    'd3d11_43': "d3dx11_43",
    'd3d8=native': "",
    'd3d9=native': "",
    'd3dimm=native': "",
    'd3dx11': "",
    'd9vk': "",
    'd9vk020': "",
    'd9vk_master': "",
    'ddr=gdi': "renderer=gdi",
    'dotnet4': "dotnet40",
    'dxvk_master': "",
    'flash': "",
    'fontsmooth-rgb': "fontsmooth=rgb",
    'gdiplus=native': "gdiplus",
    'gecko': "",
    'glsl=disabled': "",
    'jscript': "",
    'mf_install_verb': "mf",
    'mono': "",
    'mscoree': "",
    'multisampling=disabled': "",
    'powershell20': "",
    'python37': "python27",
    'settings': "",
    'vbrun2': "vb2run",
    'vc2013': "vcrun2013",
    'vcrun2005sp1': "vcrun2005",
    'vcrun20xx': "vcrun2013",
    'winegstreamer=builtin': "",
    'wsh56': "wsh57",
    'xact_jun2010': "xact",
    'xinput1_3': "xinput"
}


@app.task
def action_log_cleanup():
    """Remove zero value entries from log"""
    KeyValueStore.objects.filter(
        Q(key="spam_avatar_deleted")
        | Q(key="spam_website_deleted"),
        value=0
    ).delete()


@app.task
def populate_popularity():
    """Update the popularity field for all"""
    i = 0
    total_games = models.Game.objects.all().count()
    for game in models.Game.objects.all():
        i += 1
        if i % 10000 == 0:
            LOGGER.info("updated %s/%s games", i, total_games)
        library_count = game.libraries.all().count()
        # Only update games in libraries to speed up the process
        if library_count:
            game.popularity = library_count
            game.save(skip_precaching=True)


@app.task
def autofix_installers():
    """Automatically fix and cleanup installers"""
    stats = defaultdict(int)

    for installer in models.Installer.objects.all():
        stats["total"] += 1
        script = load_yaml(installer.content)

        # Check if installer has exe64 support
        if "exe64" in script.keys():
            stats["exe64"] += 1

        # The script is at the wrong level
        if list(script.keys()) == ["script"]:
            stats["invalid_level"] += 1
            installer.content = dump_yaml(script["script"])
            installer.save()
            continue

        # If the toplevel has "script" but it's not the only key
        if "script" in script:
            if not script["script"]:
                stats["empty_script"] += 1
                del script["script"]
                installer.content = dump_yaml(script)
                installer.save()
                continue
            stats["fd_up_script"] += 1
            script.update(script["script"])
            del script["script"]
            installer.content = dump_yaml(script)
            installer.save()
            continue
        # Check if an installer looks like a Steam game one but uses another runner
        if (
                list(script.keys()) == ["game"]
                and list(script["game"].keys()) == ["appid"]
                and installer.runner.slug != "steam"
            ):
            stats["steam_wanabee"] += 1
        if installer.runner.slug in OBSOLETE_RUNNERS:
            stats["obsolete_runners"] += 1
    return stats

@app.task
def command_stats():
    """Return statistics for used commands"""
    stats = defaultdict(int)
    for installer in models.Installer.objects.all():
        stats["total"] += 1
        script = load_yaml(installer.content)
        for step in script.get("installer", []):
            task_name = list(step.keys())[0]
            stats[task_name] += 1
    return stats


def load_winetricks_verbs(path):
    """Return list of valid winetricks verb
    path points to a file created with `winetricks list-all`
    """
    verbs = set()
    lineno = 0
    section = ""
    with open(path, encoding="utf-8") as winetrick_verb_file:
        for line in winetrick_verb_file.readlines():
            lineno += 1
            if not line or line.startswith("="):
                section = line.split()[1]
                continue
            if section == "prefix":
                continue
            verb, _rest = line.split(maxsplit=1)
            verbs.add(verb)
    return verbs


@app.task
def winetricks_stats():
    """Return statistics for Winetricks verbs"""
    valid_verbs = load_winetricks_verbs("media/winetricks-list.txt")
    stats = {
        "verbs": defaultdict(int),
        "invalid_verbs": set(),
        "wrong_runner": set(),
        "total": 0,
    }
    for installer in models.Installer.objects.all():
        stats["total"] += 1
        script = load_yaml(installer.content)
        for step in script.get("installer", []):
            task_name = list(step.keys())[0]
            if task_name != "task" or step["task"]["name"] != "winetricks":
                continue
            if installer.runner.slug != "wine":
                stats["wrong_runner"].add(installer.runner.slug)
            apps = step["task"]["app"].split()
            for app_name in apps:
                stats["verbs"][app_name] += 1
                if app_name not in valid_verbs:
                    stats["invalid_verbs"].add(app_name)
                    LOGGER.warning(
                        "Installer %s uses winetricks verb %s which is not valid",
                        installer, app_name
                    )
    return stats


def fix_winetricks_verbs():
    """Auto fix some invalid Winetricks verbs"""
    for installer in models.Installer.objects.all():
        script = load_yaml(installer.content)
        if "installer" not in script:
            continue
        new_installer = []
        changed = False
        for step in script["installer"]:
            task_name = list(step.keys())[0]
            if task_name != "task" or step["task"]["name"] != "winetricks":
                new_installer.append(step)
                continue
            apps = step["task"]["app"].split()
            new_apps = []
            for app_name in apps:
                if app_name in WINETRICKS_FIXES:
                    new_app_name = WINETRICKS_FIXES[app_name]
                    if new_app_name:
                        LOGGER.info("Replaced %s with %s", app_name, new_app_name)
                    else:
                        LOGGER.info("Removing %s", app_name)
                    new_apps.append(new_app_name)
                    changed = True
                else:
                    new_apps.append(app_name)
            if not changed:
                new_installer.append(step)
                continue
            apps = " ".join(new_apps).strip()
            if apps:
                step["task"]["app"] = apps
                new_installer.append(step)
        if changed:
            LOGGER.info("Saving %s", installer)
            script["installer"] = new_installer
            installer.content = dump_yaml(script)
            installer.save()
