import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

BASE = Path(__file__).parent.resolve()
CONFIG_DIR = BASE / "config"
LOGS_DIR = BASE / "logs"
RULES_PATH = CONFIG_DIR / "rules.json"
ACTIVITY_LOG = LOGS_DIR / "activity.log"
LAST_ACTIONS = LOGS_DIR / "last_actions.json"

# ensure dirs
CONFIG_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# rules if any other extensions needed add here
DEFAULT_RULES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx", ".csv"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".m4a"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".c", ".cpp", ".json"],
    "Executables": [".exe", ".msi", ".bat", ".sh"],
    "Others": []
}

# logging
logging.basicConfig(filename=str(ACTIVITY_LOG), level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def ensure_rules():
    """Create default rules.json if missing."""
    if not RULES_PATH.exists():
        with RULES_PATH.open("w", encoding="utf-8") as f:
            json.dump(DEFAULT_RULES, f, indent=4)
        logging.info("Created default rules.json")


def load_rules():
    ensure_rules()
    with RULES_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    normalized = {k: [e.lower() for e in v] for k, v in raw.items()}
    return normalized


def save_rules(rules: dict):
    """Save rules (human friendly)."""
    with RULES_PATH.open("w", encoding="utf-8") as f:
        json.dump(rules, f, indent=4)
    logging.info("Saved updated rules.json")


def safe_copy_folder(src: Path) -> Path:
    """
    Create a safe copy named <origname>_Organized_Copy in the same parent folder.
    If exists, append counter: _Organized_Copy (1), (2)...
    Returns path to the copy.
    """
    src = Path(src)
    parent = src.parent
    base = f"{src.name}_Organized_Copy"
    target = parent / base
    counter = 1
    while target.exists():
        target = parent / f"{base} ({counter})"
        counter += 1
    # Use copytree to duplicate folder (preserve metadata with copy_function=shutil.copy2)
    shutil.copytree(src, target, copy_function=shutil.copy2)
    logging.info(f"Created safe copy: {target}")
    return target


def human_size(nbytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if nbytes < 1024:
            return f"{nbytes:.1f}{unit}"
        nbytes /= 1024.0
    return f"{nbytes:.1f}PB"


def classify_by_type(path: Path, rules: dict) -> str:
    ext = path.suffix.lower()
    for folder, exts in rules.items():
        if ext in exts:
            return folder
    return "Others"


def classify_by_date(path: Path) -> str:
    try:
        ts = path.stat().st_ctime
    except Exception:
        ts = path.stat().st_mtime
    dt = datetime.fromtimestamp(ts)
    return f"{dt.year}_{dt.strftime('%B')}"


def classify_by_size(path: Path, small_kb=100, medium_kb=10240) -> str:
    size_kb = path.stat().st_size / 1024
    if size_kb < small_kb:
        return "Small_Files"
    elif size_kb < medium_kb:
        return "Medium_Files"
    else:
        return "Large_Files"


def plan_moves(folder: Path, mode: str) -> List[Tuple[Path, Path]]:
    """
    Plan moves inside folder (non-recursive). Return list of (src, dest).
    dest targets are inside folder/<category>/<filename>
    """
    rules = load_rules()
    files = [p for p in folder.iterdir() if p.is_file()]
    plan = []
    for f in files:
        if mode == "Type":
            cat = classify_by_type(f, rules)
        elif mode == "Date":
            cat = classify_by_date(f)
        elif mode == "Size":
            cat = classify_by_size(f)
        else:
            raise ValueError("Unknown mode")
        dest = folder / cat / f.name
        plan.append((f, dest))
    return plan


def _unique_move(src: Path, dest: Path) -> Path:
    """Move src -> dest; if dest exists add (1), (2)... Returns final dest Path."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.move(str(src), str(dest))
        return dest
    base = dest.stem
    suf = dest.suffix
    counter = 1
    while True:
        candidate = dest.parent / f"{base} ({counter}){suf}"
        if not candidate.exists():
            shutil.move(str(src), str(candidate))
            return candidate
        counter += 1


def execute_plan(plan: List[Tuple[Path, Path]], progress_cb=None) -> List[Tuple[str, str]]:
    """
    Execute moves, calling progress_cb(done, total) optionally.
    Returns list of (src_absolute, dest_absolute) for undo.
    """
    performed = []
    total = len(plan)
    for i, (src, dest) in enumerate(plan, start=1):
        try:
            final = _unique_move(src, dest)
            performed.append((str(src.resolve()), str(final.resolve())))
            logging.info(f"Moved: {src} -> {final}")
        except Exception as e:
            logging.error(f"Failed to move {src}: {e}")
        if progress_cb:
            progress_cb(i, total)
    # save last actions
    try:
        import json
        with LAST_ACTIONS.open("w", encoding="utf-8") as f:
            json.dump([{"src": s, "dest": d} for s, d in performed], f, indent=2)
        logging.info(f"Saved last actions: {LAST_ACTIONS}")
    except Exception as e:
        logging.error(f"Failed to save last_actions: {e}")
    return performed


def load_last_actions() -> List[dict]:
    import json
    if not LAST_ACTIONS.exists():
        return []
    try:
        with LAST_ACTIONS.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def undo_last_actions(progress_cb=None) -> int:
    """
    Move each recorded dest back to src. Return number restored successfully.
    """
    records = load_last_actions()
    total = len(records)
    restored = 0
    for i, rec in enumerate(records, start=1):
        src = Path(rec["src"])
        dest = Path(rec["dest"])
        try:
            if dest.exists() and dest.is_file():
                src.parent.mkdir(parents=True, exist_ok=True)
                # if src exists, make a unique name for restored file
                final = _unique_move(dest, src)
                logging.info(f"Restored: {dest} -> {final}")
                restored += 1
            else:
                logging.warning(f"Cannot restore, dest missing: {dest}")
        except Exception as e:
            logging.error(f"Failed to restore {dest} -> {src}: {e}")
        if progress_cb:
            progress_cb(i, total)
    # remove last actions file
    try:
        LAST_ACTIONS.unlink()
    except Exception:
        pass
    logging.info(f"Undo finished. Restored {restored}/{total}")
    return restored
