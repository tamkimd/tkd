from __future__ import annotations

import json
from pathlib import Path

from tkd.common.models import MCPArtifact


def load_mcp(path: Path) -> MCPArtifact:
    candidate = path if path.suffix == ".json" else path / "mcp.json"
    if not candidate.exists():
        raise ValueError(f"Missing MCP config at {path}")
    config = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError(f"MCP config must be a JSON object: {candidate}")
    return MCPArtifact(name=path.stem.lower(), config=config, path=path)
