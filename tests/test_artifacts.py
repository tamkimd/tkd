from __future__ import annotations

from pathlib import Path

from tkd.artifacts.skill import load_skill
from tests.conftest import write


def test_skill_frontmatter_tolerates_extra_yaml_like_lines(tmp_path: Path) -> None:
    skill_dir = tmp_path / "theme-factory"
    write(
        skill_dir / "SKILL.md",
        (
            "---\n"
            "name: theme-factory\n"
            "description: Toolkit for styling artifacts.\n"
            "tags:\n"
            "  - design\n"
            "  - presentations\n"
            "license: Complete terms in LICENSE.txt\n"
            "---\n\n"
            "Use this skill for themed artifacts.\n"
        ),
    )

    artifact = load_skill(skill_dir)

    assert artifact.name == "theme-factory"
    assert artifact.description == "Toolkit for styling artifacts."
