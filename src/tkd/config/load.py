from __future__ import annotations

import json

from tkd.common.models import TkdConfig


def load_config(path):
    if path.suffix != ".json":
        raise ValueError("Only JSON config is supported. Use tkd.json.")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Config root must be a JSON object.")
    return TkdConfig.model_validate(raw)
