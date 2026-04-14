import json
from pathlib import Path

BASE = Path(__file__).parent.resolve()
CONFIG_DIR = BASE / "config"
RULES_PATH = CONFIG_DIR / "rules.json"

CONFIG_DIR.mkdir(exist_ok=True)


def load_rules():
    if not RULES_PATH.exists():
        # create empty default to avoid crash (write simple empty Others)
        default = {"Images": [".jpg", ".png"], "Documents": [".pdf", ".txt"], "Others": []}
        with RULES_PATH.open("w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
        return default
    with RULES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # ensure list of extensions per key
    norm = {}
    for k, v in data.items():
        if isinstance(v, list):
            norm[k] = [e.lower() for e in v]
        else:
            norm[k] = []
    return norm


def save_rules(rules_dict):
    # basic normalization: ensure extensions begin with dot and lowercase
    clean = {}
    for cat, exts in rules_dict.items():
        clean_list = []
        for e in exts:
            if not e:
                continue
            e = e.strip().lower()
            if not e.startswith("."):
                e = "." + e
            clean_list.append(e)
        clean[cat.strip()] = sorted(list(set(clean_list)))
    with RULES_PATH.open("w", encoding="utf-8") as f:
        json.dump(clean, f, indent=4)
