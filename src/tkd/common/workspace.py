from __future__ import annotations

import shutil
from pathlib import Path

from tkd.common.files import remove_existing_path
from tkd.common.models import PathList, SharedAgentPayload


def shared_agents_root(workspace_root: Path) -> Path:
    return workspace_root / ".agents"


def build_shared_agents_layer(payload: SharedAgentPayload, workspace_root: Path) -> PathList:
    shared_root = shared_agents_root(workspace_root)
    shared_root.mkdir(parents=True, exist_ok=True)
    written = []
    skills_root = shared_root / "skills"
    rules_root = shared_root / "rules"
    workflows_root = shared_root / "workflows"
    skills_root.mkdir(parents=True, exist_ok=True)
    rules_root.mkdir(parents=True, exist_ok=True)
    workflows_root.mkdir(parents=True, exist_ok=True)

    for skill in payload.skills:
        dest = skills_root / skill.name
        remove_existing_path(dest)
        shutil.copytree(skill.path, dest)
        written.append(dest)
    for rule in payload.rules:
        dest = rules_root / f"{rule.name}.md"
        dest.write_text(rule.content.strip() + "\n", encoding="utf-8")
        written.append(dest)
    for command in payload.commands:
        dest = workflows_root / f"{command.name}.md"
        body = f"---\ndescription: {command.description}\n---\n\n{command.template.strip()}\n"
        dest.write_text(body, encoding="utf-8")
        written.append(dest)
    return written
