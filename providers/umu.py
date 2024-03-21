import logging
import os
import json
from collections import defaultdict
from typing import List, Tuple

import git
import requests
from django.conf import settings
from django.utils import timezone

from games.steam import create_game_from_steam_appid
from providers.models import Provider, ProviderGame

LOGGER = logging.getLogger(__name__)

PROTONFIXES_URL = "https://github.com/Open-Wine-Components/umu-protonfixes"
UMU_API_URL = "https://umu.openwinecomponents.org/umu_api.php"
PROTONFIXES_PATH = os.path.join(settings.MEDIA_ROOT, "protonfixes")
PROTON_PATCHES_STEAM_IDS = os.path.join(settings.MEDIA_ROOT, "proton-steamids.txt")
UMU_GAMES_PATH = os.path.join(settings.MEDIA_ROOT, "umu-games.json")

def fix_steam_ids():
    games_updated = 0
    provider_games = ProviderGame.objects.filter(
        provider__name="steam", internal_id__isnull=True
    )
    provider_games_cnt = provider_games.count()
    for pg in provider_games:
        pg.internal_id = pg.slug
        pg.save()
        games_updated += 1
        if (games_updated % 1000) == 0:
            print(f"Updated {games_updated}/{provider_games_cnt}")
    return games_updated


def update_repository():
    if os.path.exists(PROTONFIXES_PATH):
        repo = git.Repo(PROTONFIXES_PATH)
        remote = git.remote.Remote(repo, "origin")
        remote.pull()
    else:
        repo = git.Repo.clone_from(PROTONFIXES_URL, PROTONFIXES_PATH)


def get_umu_api_games():
    response = requests.get(UMU_API_URL)
    games_by_id = {}
    for entry in response.json():
        appid = entry["umu_id"]
        if appid in games_by_id:
            games_by_id[appid].append(entry)
        else:
            games_by_id[appid] = [entry]
    return games_by_id


def get_game_ids(gamefix_folder: str) -> set:
    fixes = os.listdir(os.path.join(PROTONFIXES_PATH, gamefix_folder))
    game_ids = set()
    for fix in fixes:
        base, ext = os.path.splitext(fix)
        if ext != ".py":
            continue
        if base in ("__init__", "default", "winetricks-gui"):
            continue
        if base.startswith("umu-"):
            base = base.split("umu-")[1]
        game_ids.add(base)
    return game_ids


def get_proton_patch_ids() -> set:
    game_ids = set()
    with open(PROTON_PATCHES_STEAM_IDS) as patch_ids_file:
        for line in patch_ids_file.readlines():
            appid = line.strip()
            game_ids.add(appid)
    return game_ids


def get_all_fixes_ids() -> set:
    """Get IDs for all games from all stores + Proton patches"""
    game_ids = set()
    for folder in iter_gamefix_folders():
        for game_id in get_game_ids(folder):
            game_ids.add(game_id)
    return game_ids.union(get_proton_patch_ids())


def check_lutris_associations():
    umu_games = get_umu_api_games()
    fixes_ids = get_all_fixes_ids()
    seen_fixes = set()
    stats = defaultdict(int)
    stats["fixes"] = len(fixes_ids)
    stats["api_games"] = len(umu_games)
    for game_id in umu_games:
        steam_id = None
        for store_game in umu_games[game_id]:
            if steam_id:
                continue
            steam_id = store_game["umu_id"].split("umu-")[1]
            if steam_id not in fixes_ids:
                stats["no fixes"] += 1
            else:
                seen_fixes.add(steam_id)
                stats["with fix"] += 1
            if not steam_id.isnumeric() or steam_id == store_game["codename"]:
                stats["non steam"] += 1
                steam_id = None
            if steam_id:
                try:
                    steam_provider_game = ProviderGame.objects.get(
                        provider__name="steam", internal_id=steam_id
                    )
                except ProviderGame.DoesNotExist:
                    LOGGER.error("Steam game with ID %s not found", steam_id)
                    create_game_from_steam_appid(steam_id)
                    stats["steam game not found"] = steam_id
                    continue
                stats["in api"] += 1
                get_other_provider_games(steam_provider_game)

    steam_games_not_found = set()
    provider_games = []
    for game_id in fixes_ids - seen_fixes:
        try:
            steam_provider_game = ProviderGame.objects.get(
                provider__name="steam", internal_id=game_id
            )
            provider_games += get_other_provider_games(steam_provider_game)
            stats["fix not in DB"] += 1
        except ProviderGame.DoesNotExist:
            steam_games_not_found.add(game_id)

    if steam_games_not_found:
        LOGGER.warning("Some Steam games are not in the Lutris database")
        LOGGER.warning(steam_games_not_found)
    output_csv(provider_games)
    return stats


def output_csv(provider_games: List[Tuple]):
    """Print to the terminal data that can be re-imported to the umu database1"""
    for provider_game, steam_game in provider_games:
        print(
            f"{provider_game.name},{provider_game.provider.name},{provider_game.slug},umu-{steam_game.slug},,"
        )


def get_other_provider_games(steam_provider_game):
    lutris_games = steam_provider_game.games.all()
    if not lutris_games:
        LOGGER.warning("No associated Lutris game for %s", steam_provider_game)
        create_game_from_steam_appid(steam_provider_game.internal_id)
        return []
    if lutris_games.count() > 1:
        LOGGER.warning("More than one Lutris game for %s", steam_provider_game)
        for lutris_game in lutris_games:
            LOGGER.warning(lutris_game)
    lutris_game = lutris_games[0]
    provider_games = []
    for provider_game in lutris_game.provider_games.exclude(
        provider__name__in=("igdb", "steam")
    ):
        provider_games.append((provider_game, steam_provider_game))
    return provider_games


def check_steam_to_lutris_matches():
    """Check that every Steam game in the umu database has a corresponding Lutris game
    If not, create them.
    """
    steam_ids: set = get_game_ids("gamefixes-steam").union(get_proton_patch_ids())
    steam_games = ProviderGame.objects.filter(
        provider__name="steam", internal_id__in=steam_ids
    )
    matched_steam_ids = set()
    for steam_game in steam_games:
        matched_steam_ids.add(steam_game.internal_id)
        for game in steam_game.games.all():
            providers = []
            for prov in game.provider_games.exclude(provider__name="igdb"):
                providers.append(prov.provider.name)
            print(steam_game.name, ":", ", ".join(providers))

    unmatched_games = steam_ids - matched_steam_ids
    if unmatched_games:
        print("Unmatched IDs")
        for appid in unmatched_games:
            create_game_from_steam_appid(appid)
    else:
        print("All games matched")


def parse_python_fix(file_path):
    with open(file_path, "r", encoding="utf-8") as python_script:
        script_content = python_script.readlines()
    fixes = []
    fixes_started = False
    complex_script = False
    for line in script_content:
        if line.startswith("def main"):
            fixes_started = True
            continue
        if not fixes_started:
            continue
        if line.strip().startswith(('"""', "#")) or not line.strip():
            continue
        if line.strip().startswith("util"):
            line = line.strip().replace("util.", "")
            if line.startswith(
                ("winedll_override", "set_environment", "replace_command")
            ):
                line = line.replace("', '", "=").replace("','", "=")
            if not line.startswith(("regedit_add", "append_arguments")):
                line = line.replace("('", ": ").replace("()", "")
            if not line.startswith(("set_ini_options")):
                line = line.replace("')", "")
            fixes.append(line.strip())
        else:
            complex_script = True
    if complex_script:
        fixes.append("additional_fixes")
    return fixes


def iter_gamefix_folders():
    for path in os.listdir(os.path.join(PROTONFIXES_PATH)):
        if not path.startswith("gamefixes-"):
            continue
        yield path


def parse_protonfixes(gamefix_folder):
    fixes = {}
    store_path = os.path.join(PROTONFIXES_PATH, gamefix_folder)
    fix_files = os.listdir(store_path)
    for fix in fix_files:
        appid, ext = os.path.splitext(fix)
        if appid in ("default", "__init__"):
            continue
        fixes[appid] = parse_python_fix(os.path.join(store_path, fix))
    return fixes


def convert_to_lutris_script(protonfix):
    ignored_tasks = (
        "disable_protonaudioconverter",
        "additional_fixes",
        "use_seccomp",
        "_mk_syswow64",
        "create_dosbox_conf",
        "set_cpu_topology_nosmt",
        "set_xml_options",
        "disable_uplay_overlay",
        "disable_nvapi",
    )
    installer = {"game": {}, "installer": [], "wine": {}, "system": {}}
    script = []
    for task in protonfix:
        if task.startswith("protontricks"):
            verb = task.split(": ")[1]
            script.append({"task": {"name": "winetricks", "app": verb}})
            continue
        if task.startswith(ignored_tasks):
            # Ignore, only applicable to Proton
            continue
        if task.startswith("append_argument"):
            installer["game"]["args"] = task.split(": ")[1]
            continue
        if task.startswith("winedll_override"):
            if "overrides" not in installer["wine"]:
                installer["wine"]["overrides"] = {}
            key, value = task.split(": ")[1].split("=", maxsplit=1)
            installer["wine"]["overrides"][key] = value
            continue
        if task.startswith(("set_ini_options", "regedit_add")):
            # TODO
            continue
        if task.startswith("set_environment"):
            if "env" not in installer["system"]:
                installer["system"]["env"] = {}
            key, value = task.split(": ")[1].split("=", maxsplit=1)
            installer["system"]["env"][key] = value
            continue
        if task.startswith("replace_command"):
            installer["game"]["exe"] = task.split(": ")[1]
            continue
        if task.startswith("install_eac_runtime"):
            installer["wine"]["eac"] = True
            continue
        if task.startswith("install_battleye_runtime"):
            installer["wine"]["battleye"] = True
            continue
        if task.startswith("disable_esync"):
            installer["wine"]["esync"] = False
            continue
        if task.startswith("disable_fsync"):
            installer["wine"]["fsync"] = False
            continue
        if task.startswith("set_cpu_topology_limit"):
            installer["system"]["single_cpu"] = True
            installer["system"]["limit_cpu_count"] = task.split("(")[1].rstrip(")")
            continue
        raise ValueError("unhandled task: %s in %s" % (task, protonfix))
    installer["installer"] = script
    return {k: v for k, v in installer.items() if v}


def import_umu_games():
    """Load umu games from the API to the Lutris DB"""
    api_games = get_umu_api_games()
    fix_ids = get_all_fixes_ids()
    provider = Provider.objects.get(name="umu")
    stats = {
        "api-games": len(api_games),
        "fixes": len(fix_ids),
        "created": 0,
        "updated": 0,
        "skipped": 0,

    }
    for game_id in api_games:
        if game_id.split("umu-")[1] not in fix_ids:
            LOGGER.info("Skipping %s, it has no fix", game_id)
            stats["skipped"] += 1
            continue
        provider_game, created = ProviderGame.objects.get_or_create(
            internal_id=game_id,
            provider=provider,
        )
        if created:
            LOGGER.info("Created %s", game_id)
            stats["created"] += 1
        else:
            LOGGER.info("Updated %s", game_id)
            stats["updated"] += 1
        provider_game.slug = game_id
        provider_game.name = api_games[game_id][0]["title"]
        provider_game.updated_at = timezone.now()
        provider_game.metadata = api_games[game_id]
        provider_game.save()
    return stats


def export_umu_games():
    """Export umu games to a JSON that can be used by the client"""
    provider_games = ProviderGame.objects.filter(provider__name="umu")
    output = []
    for provider_game in provider_games:
        for game in provider_game.metadata:
            output.append({
                "name": game["title"],
                "store": game["store"],
                "appid": game["codename"],
                "notes": game["notes"],
                "umu_id": game["umu_id"],
            })
    return output


def save_umu_games():
    """Save the list of umu games to a file"""
    umu_games = export_umu_games()
    with open(UMU_GAMES_PATH, "w") as umu_file:
        json.dump(umu_games, umu_file, indent=2)