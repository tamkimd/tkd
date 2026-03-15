from __future__ import annotations

import re
from pathlib import Path

from tkd.common.models import SkillArtifact

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_VALID_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _parse_frontmatter_block(block: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    current_key = None
    for raw_line in block.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line[:1].isspace() or raw_line.lstrip().startswith("- "):
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        current_key = key.strip()
        parsed[current_key] = value.strip().strip("'\"")
    return parsed


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER.match(text)
    if not match:
        raise ValueError("SKILL.md must start with frontmatter delimited by ---")
    frontmatter = _parse_frontmatter_block(match.group(1))
    body = text[match.end() :].strip()
    return frontmatter, body


def load_skill(path: Path) -> SkillArtifact:
    skill_file = path / "SKILL.md"
    if not skill_file.exists():
        raise ValueError(f"Missing SKILL.md in {path}")
    frontmatter, body = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not name or not description:
        raise ValueError(f"Skill at {path} must define name and description")
    if not _VALID_NAME.match(name):
        raise ValueError(f"Invalid skill name: {name}")
    if path.name != name:
        raise ValueError(f"Skill directory name {path.name!r} must match frontmatter name {name!r}")
    if not body:
        raise ValueError(f"Skill {name} must include body instructions")
    return SkillArtifact(name=name, description=description, path=path)
