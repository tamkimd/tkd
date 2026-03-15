from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from tkd.common.models import JSONObject


def user_home_dir() -> Path:
    return Path(os.environ.get("HOME") or os.environ.get("USERPROFILE") or "~").expanduser()


def remove_existing_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_file():
        path.unlink()
        return
    shutil.rmtree(path)


def mirror_path(source: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    remove_existing_path(dest)
    if source.is_dir():
        shutil.copytree(source, dest)
    else:
        shutil.copy2(source, dest)
    return dest


def copy_path(source: Path, dest: Path) -> Path:
    return mirror_path(source, dest)


def merge_json_object(target: Path, content: JSONObject) -> Path:
    merged = {}
    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        if isinstance(existing, dict):
            merged.update(existing)
    for key, value in content.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            combined = dict(merged[key])
            combined.update(value)
            merged[key] = combined
        else:
            merged[key] = value
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
