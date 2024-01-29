import os
import git
import yaml
from lutris.api import get_game_service_api_page


PROTONFIXES_URL = "https://github.com/Open-Wine-Components/ULWGL-protonfixes"
PROTONFIXES_PATH = "protonfixes"


def update_repository():
    if os.path.exists(PROTONFIXES_PATH):
        repo = git.Repo(PROTONFIXES_PATH)
        remote = git.remote.Remote(repo, "origin")
        remote.pull()
    else:
        repo = git.Repo.clone_from(PROTONFIXES_URL, PROTONFIXES_PATH)


def get_game_ids(store="Steam"):
    fixes = os.listdir(os.path.join(PROTONFIXES_PATH, "gamefixes-%s" % store))
    game_ids = []
    for fix in fixes:
        base, ext = os.path.splitext(fix)
        if ext != ".py":
            continue
        if base in ("__init__", "default"):
            continue
        game_ids.append(base)
    return game_ids


def get_lutris_games(appids, service="steam", page=1):
    return get_game_service_api_page(service, appids, page)


def print_lutris_matches():
    steam_ids = get_game_ids()
    response = get_lutris_games(steam_ids)
    for game in response["results"]:
        print(
            game["name"],
            ", ".join(
                [f"{prov['service']}:{prov['slug']}" for prov in game["provider_games"]]
            ),
        )
    matched_steam_ids = [
        [p["slug"] for p in g["provider_games"] if p["service"] == "steam"][0]
        for g in response["results"]
    ]
    print("Unmatched IDs")
    print(set(steam_ids) - set(matched_steam_ids))


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


def parse_protonfixes(store="Steam"):
    fixes = {}
    store_path = os.path.join(PROTONFIXES_PATH, "gamefixes-%s" % store)
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
        "disable_nvapi"
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
    return {k: v for k,v in installer.items() if v}


if __name__ == "__main__":
    update_repository()
    print_lutris_matches()
    # results = parse_protonfixes()
    # print(json.dumps(results, indent=2))
    # for key, fix in results.items():
    #     res = convert_to_lutris_script(fix)
    #     if res:
    #         print(key)
    #         print(yaml.dump(res))
