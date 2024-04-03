# pylint:disable=no-member
"""Celery tasks for account related jobs"""

from collections import defaultdict
from celery.utils.log import get_task_logger
from django.db.models import Q

from common.util import load_yaml, dump_yaml
from common.models import KeyValueStore
from runners.models import RunnerVersion, Runner
from games import models

from lutrisweb.celery import app

LOGGER = get_task_logger(__name__)


OBSOLETE_RUNNERS = ("winesteam", "browser")

# Build used for League of Legends games
CURRENT_LOL_BUILD = "wine-ge-lol-8-27-x86_64"


# The following builds will be unpinned.
CURRENT_BUILDS = (
    "wine-ge-8-25-x86_64",
    "lutris-GE-Proton8-26-x86_64",
    "lutris-GE-Proton8-25-x86_64",
    "lutris-GE-Proton8-24-x86_64",
    "lutris-GE-Proton8-23-x86_64",
    "lutris-GE-Proton8-22-x86_64",
    "lutris-GE-Proton8-21-x86_64",
    "lutris-GE-Proton8-20-x86_64",
    "lutris-GE-Proton8-19-x86_64",
    "lutris-GE-Proton8-18-x86_64",
    "lutris-GE-Proton8-17-x86_64",
    "lutris-GE-Proton8-16-x86_64",
    "lutris-GE-Proton8-15-x86_64",
    "lutris-GE-Proton8-14-x86_64",
    "lutris-GE-Proton8-13-x86_64",
    "lutris-GE-Proton8-12-x86_64",
    "lutris-GE-Proton8-10-x86_64",
    "lutris-GE-Proton8-8-x86_64",
    "lutris-GE-Proton8-7-x86_64",
    "lutris-GE-Proton8-6-x86_64",
    "lutris-GE-Proton8-5-x86_64",
    "lutris-GE-Proton8-4-x86_64",
    "lutris-5.7-11-x86_64",
)

RUNNER_DEFAULTS = {
    "dxvk": True,
    "vkd3d": True,
    "esync": True,
    "fsync": True,
    "eac": True,
    "d3d_extras": True,
    "dxvk_nvapi": True,
    "battleye": True,
    "dgvoodoo2": False,
    "Desktop": False,
    "show_debug": "-all",
}

# Fixes typos and non existent Winetricks verbs.
# Empty string means the task will be removed
WINETRICKS_FIXES = {
    "--force": "",
    "--unattended": "",
    "-f": "",
    "adobeair": "",
    "corfonts": "corefonts",
    "ariel": "arial",
    "d3d11_43": "d3dx11_43",
    "d3d8=native": "",
    "d3d9=native": "",
    "d3dimm=native": "",
    "d3dx11": "",
    "d9vk": "",
    "d9vk020": "",
    "d9vk_master": "",
    "ddr=gdi": "renderer=gdi",
    "dotnet4": "dotnet40",
    "dxvk_master": "",
    "flash": "",
    "fontsmooth-rgb": "fontsmooth=rgb",
    "gdiplus=native": "gdiplus",
    "gecko": "",
    "glsl=disabled": "",
    "jscript": "",
    "mf_install_verb": "mf",
    "mono": "",
    "mscoree": "",
    "multisampling=disabled": "",
    "powershell20": "",
    "python37": "python27",
    "settings": "",
    "vbrun2": "vb2run",
    "vc2013": "vcrun2013",
    "vcrun2005sp1": "vcrun2005",
    "vcrun20xx": "vcrun2013",
    "winegstreamer=builtin": "",
    "wsh56": "wsh57",
    "xact_jun2010": "xact",
    "xinput1_3": "xinput",
}

VALID_INSTALLER_KEYS = (
    "game",
    "installer",
    "files",
    "system",
    "custom-name",
    "requires",
    "extends",
    "variables",
    "install_complete_text",
    "require-libraries",  # ?? maybe not
    "require-binaries",

    "wine",
    "dosbox",
    "libretro",
    "zdoom",
    "scummvm",
    "winesteam",  # Deprecated
    "vice",
    "fsuae",
    "steam",  # But why
    "linux",
    "web",

    "gogid",  # Should be removed later
    "humblestoreid",  # Should be removed later
)

INVALID_INSTALLER_KEYS = (
    "Requires",
    "Scummvm",
    "file",
    "install",
    "year",
    "task",
    "pulse_latency",
    "format",
    "dst",
    "game_slug",
    "name",
    "-Wine",
    "-execute",
    "execute",
    "arch",
    "fullscreen",
    "overrides",
    "steamid",
    "Main_file",
    "browser",
    "requires-binaries",
    "require_binaries",
    "env",
    "insert-disc",
)

INVALID_INSTALLER_KEYS_DELETE = (
    "Desktop",
    "appid",
    "custum-name",
)


@app.task
def action_log_cleanup():
    """Remove zero value entries from log"""
    KeyValueStore.objects.filter(
        Q(key="spam_avatar_deleted") | Q(key="spam_website_deleted"), value=0
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
def auto_accept_installers():
    for f in models.InstallerDraft.objects.filter(
        draft=False, user__username="vanstaveren"
    ):
        f.accept()


@app.task
def autofix_installers():
    """Automatically fix and cleanup installers"""
    stats = defaultdict(int)
    stats["invalid_keys"] = defaultdict(int)
    stats["invalid_installers"] = set()
    stats["steam_wanabee"] = set()
    stats["exe_conflict"] = set()

    for installer in models.Installer.objects.all():
        stats["total"] += 1
        script = load_yaml(installer.content)
        installer_keys = list(script.keys())
        for key in installer_keys:
            if key not in VALID_INSTALLER_KEYS:
                stats["invalid_keys"][key] += 1
                if key in INVALID_INSTALLER_KEYS:
                    stats["invalid_installers"].add((installer.slug, key))
                if key in INVALID_INSTALLER_KEYS_DELETE:
                    del script[key]
                    installer.content = dump_yaml(script)
                    installer.save()


        # Check if installer has exe64 support
        if "exe64" in script.keys():
            if "game" not in script:
                script["game"] = {}
            script["game"]["exe"] = script["exe64"]
            if "exe" in script.keys():
                script["game"]["launch_configs"] = []
                script["game"]["launch_configs"].append({"exe": script["exe"], "name": "32 bit version"})
                del(script["exe"])
            del(script["exe64"])
            installer.content = dump_yaml(script)
            installer.save()
            stats["exe64"] += 1
        if "exe" in script.keys() and "exe64" not in script.keys():
            if "game" not in script:
                script["game"] = {}
            if "exe" not in script["game"] or script["game"]["exe"].strip() == script["exe"].strip():
                script["game"]["exe"] = script["exe"]
                del(script["exe"])
                installer.content = dump_yaml(script)
                installer.save()
                stats["exe"] += 1
            else:
                stats["exe_conflict"].add(installer.slug)

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
        steam_runner = Runner.objects.get(slug="steam")
        # Check if an installer looks like a Steam game one but uses another runner
        if (
            list(script.keys()) == ["game"]
            and list(script["game"].keys()) == ["appid"]
            and installer.runner.slug != "steam"
        ):
            stats["steam_wanabee"].add(installer.slug)
            installer.runner = steam_runner
            installer.save()

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
                        installer,
                        app_name,
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


@app.task
def remove_defaults():
    """Removes some directives from installers that represent the default behavior of the client
    such as dxvk: true or esync: true"""
    stats = defaultdict(int)
    stats["keys"] = set()
    for installer in models.Installer.objects.all():
        script = load_yaml(installer.content)
        if installer.runner.slug not in script:
            continue
        stats["total"] += 1
        runner_config = script[installer.runner.slug]
        if runner_config is None:
            stats["empty_configs"] += 1
            script.pop(installer.runner.slug)
            installer.content = dump_yaml(script)
            installer.save()
            continue
        changed = False
        for key, default_value in RUNNER_DEFAULTS.items():
            if key in runner_config and runner_config[key] == default_value:
                LOGGER.info("Removing %s from %s", key, installer)
                runner_config.pop(key)
                changed = True
        for key in runner_config:
            stats["keys"].add(key)
        if changed:
            if runner_config:
                stats["updated_config"] += 1
                script[installer.runner.slug] = runner_config
            else:
                stats["removed_config"] += 1
                script.pop(installer.runner.slug)
            installer.content = dump_yaml(script)
            installer.save()
    return stats


@app.task
def fix_and_unpin_wine_versions():
    """Removes Wine versions that reference non existant builds or the current default"""
    published_versions = RunnerVersion.objects.filter(runner__slug="wine")
    stats = {
        "versions": defaultdict(list),
        "games": defaultdict(set),
        "published_versions": {
            f"{v.version}-{v.architecture}": 0 for v in published_versions
        },
        "updated_config": 0,
        "removed_config": 0,
        "lol_updates": 0,
    }
    for installer in models.Installer.objects.all():
        script = load_yaml(installer.content)
        runner = installer.runner.slug
        if runner not in script:
            continue
        runner_config = script[runner]
        if "version" not in runner_config:
            continue
        changed = False
        version = str(runner_config["version"])
        stats["versions"][version].append(installer.slug)
        stats["games"][installer.game.slug].add(version)

        # Handle current builds and non existant builds
        if (
            runner_config["version"] in CURRENT_BUILDS
            or runner_config["version"] not in stats["published_versions"]
        ):
            version = runner_config.pop("version")
            LOGGER.info("Unpinning %s from %s", version, installer)
            changed = True
        elif runner_config["version"]:
            stats["published_versions"][runner_config["version"]] += 1

        # Save changes
        if changed:
            if runner_config:
                stats["updated_config"] += 1
                script[installer.runner.slug] = runner_config
            else:
                stats["removed_config"] += 1
                script.pop(installer.runner.slug)
            installer.content = dump_yaml(script)
            installer.save()

    # Update League of Legends installers
    for installer in models.Installer.objects.filter(game__slug="league-of-legends"):
        script = load_yaml(installer.content)
        if "wine" not in script:
            script["wine"] = {}
        if script["wine"].get("version") != CURRENT_LOL_BUILD:
            script["wine"]["version"] = CURRENT_LOL_BUILD
            installer.content = dump_yaml(script)
            installer.save()
    return stats


def migrate_unzip_installers():
    """Migrate unzip usage to extract task"""
    stats = {
        "total": 0,
        "keep": 0,
        "deleted": 0,
        "nofiles": 0,
    }
    for installer in models.Installer.objects.filter(
        content__icontains="files/tools/unzip"
    ):
        stats["total"] += 1
        script = load_yaml(installer.content)
        if "files" not in script:
            stats["nofiles"] += 1
            continue
        stepnames = [list(step.keys())[0] for step in script["installer"]]
        if installer.version in ("GOG", "GOG.com") and stepnames == [
            "extract",
            "execute",
            "rename",
        ]:
            print("Deleting", installer)
            stats["deleted"] += 1
            installer.delete()
            continue
        stats["keep"] += 1
    return stats
