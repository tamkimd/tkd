from __future__ import annotations

from pathlib import Path

from tkd.artifacts.skill import parse_frontmatter
from tkd.common.models import CommandArtifact


def load_command(path: Path) -> CommandArtifact:
    candidate = path if path.suffix in {".md", ".markdown"} else path.with_suffix(".md")
    if not candidate.exists():
        raise ValueError(f"Missing command file at {path}")
    text = candidate.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        frontmatter, body = parse_frontmatter(text)
    else:
        frontmatter, body = {}, text.strip()
    name = str(frontmatter.get("name") or candidate.stem)
    description = str(frontmatter.get("description") or f"Run {name}")
    if not body:
        raise ValueError(f"Command {name} must include body instructions")
    return CommandArtifact(
        name=name,
        description=description,
        template=body,
        path=candidate,
        metadata=frontmatter if isinstance(frontmatter, dict) else {},
    )
