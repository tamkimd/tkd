from __future__ import annotations

from pathlib import Path

from tkd.common.models import RuleArtifact


def load_rule(path: Path) -> RuleArtifact:
    if path.is_dir():
        candidate = path / "RULE.md"
    else:
        candidate = path
    if not candidate.exists():
        raise ValueError(f"Missing rule content at {path}")
    content = candidate.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Rule {path} is empty")
    return RuleArtifact(name=path.stem.lower(), content=content, path=path)
