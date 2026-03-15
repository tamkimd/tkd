from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from tkd.adapters.agent_layouts import get_agent_layout
from tkd.common.files import (
    merge_json_object,
    mirror_path,
    user_home_dir,
)
from tkd.common.models import (
    CommandArtifact,
    InstallPayload,
    MCPArtifact,
    RuleArtifact,
    SkillArtifact,
)
from tkd.common.workspace import shared_agents_root


class AgentAdapter:
    name: str
    config_dir: str = ""
    supports_skills: bool = True
    supports_rules: bool = True
    supports_commands: bool = True
    supports_mcp: bool = False

    # -- Template method ----------------------------------------------------------

    async def install(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        written = self._do_install_skills(payload, workspace_root)
        written.extend(self._do_install_rules(payload, workspace_root))
        written.extend(self._do_install_commands(payload, workspace_root))
        written.extend(self._do_install_mcp(payload, workspace_root))
        return written

    def _do_install_skills(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        return self._install_shared_artifacts(
            workspace_root,
            "skills",
            payload.skills,
        )

    def _do_install_rules(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        return self._install_shared_artifacts(
            workspace_root,
            "rules",
            payload.rules,
        )

    def _do_install_commands(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        return self._install_shared_artifacts(
            workspace_root,
            "commands",
            payload.commands,
        )

    def _do_install_mcp(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        if not payload.mcp:
            return []
        servers = {a.name: a.config for a in payload.mcp}
        return [self._write_json(self._mcp_target(workspace_root), {"mcpServers": servers})]

    # -- Shared artifact mirroring ------------------------------------------------

    def _install_shared_artifacts(
        self,
        workspace_root: Path,
        category: str,
        artifacts: list[SkillArtifact] | list[RuleArtifact] | list[CommandArtifact],
        target_root: Path | None = None,
    ) -> list[Path]:
        shared_root = shared_agents_root(workspace_root)
        written: list[Path] = []
        for artifact in artifacts:
            source = self._shared_artifact_path(shared_root, category, artifact)
            if target_root is not None:
                dest = target_root / artifact.name
            elif category == "skills":
                dest = self.config_root(workspace_root) / "skills" / artifact.name
            else:
                dest = self._layout_artifact_target(workspace_root, category, artifact)
            written.append(mirror_path(source, dest))
        return written

    # -- Layout target resolution -------------------------------------------------

    def config_root(self, workspace_root: Path) -> Path:
        if not self.config_dir:
            raise ValueError(f"{self.name} does not define config_dir")
        return workspace_root / self.config_dir

    def _layout(self):
        return get_agent_layout(self.name)

    def _resolve_layout_path(self, workspace_root: Path, layout_path: str) -> Path:
        if layout_path.startswith("~/"):
            return user_home_dir() / layout_path[2:]
        return workspace_root / layout_path

    def _layout_artifact_target(self, workspace_root: Path, category: str, artifact) -> Path:
        layout = getattr(self._layout(), category if category != "commands" else "commands")
        if category == "rules":
            layout = self._layout().rules
        elif category == "commands":
            layout = self._layout().commands
        if layout.mode != "directory" or not layout.path:
            raise ValueError(f"{self.name} does not support directory {category} targets")
        return (
            self._resolve_layout_path(workspace_root, layout.path)
            / f"{artifact.name}{layout.suffix}"
        )

    def _rules_document_target(self, workspace_root: Path) -> Path:
        layout = self._layout().rules
        if layout.mode != "document" or not layout.path:
            raise ValueError(f"{self.name} does not support rule documents")
        return self._resolve_layout_path(workspace_root, layout.path)

    def _commands_container(self, workspace_root: Path) -> Path:
        layout = self._layout().commands
        if layout.mode != "directory" or not layout.path:
            raise ValueError(f"{self.name} does not support directory command targets")
        return self._resolve_layout_path(workspace_root, layout.path)

    def _mcp_target(self, workspace_root: Path) -> Path:
        layout = self._layout().mcp
        if layout.mode not in {"file", "global_file", "embedded"} or not layout.path:
            raise ValueError(f"{self.name} does not define an MCP file target")
        return self._resolve_layout_path(workspace_root, layout.path)

    def _shared_artifact_path(self, shared_root: Path, category: str, artifact) -> Path:
        _dirs = {"skills": "skills", "rules": "rules", "commands": "workflows"}
        _suffixes = {"skills": "", "rules": ".md", "commands": ".md"}
        name = artifact.name + _suffixes[category]
        return shared_root / _dirs[category] / name

    # -- Write helpers ------------------------------------------------------------

    def _write_joined_rules_doc(
        self,
        target: Path,
        rules: list[RuleArtifact],
    ) -> list[Path]:
        if not rules:
            return []
        content = "\n\n".join(rule.content for rule in rules)
        return [self._write_text(target, content + "\n")]

    def _write_frontmatter_commands(
        self,
        workspace_root: Path,
        commands: list[CommandArtifact],
    ) -> list[Path]:
        command_root = self._commands_container(workspace_root)
        written: list[Path] = []
        for command in commands:
            desc = command.description
            desc_value = json.dumps(desc) if any(c.isspace() for c in desc) else desc
            written.append(
                self._write_text(
                    target=command_root / f"{command.name}.md",
                    content=f"---\ndescription: {desc_value}\n---\n\n{command.template.strip()}\n",
                )
            )
        return written

    def _merge_json_mcp_servers(self, target: Path, artifacts: list[MCPArtifact]) -> list[Path]:
        if not artifacts:
            return []
        servers = {a.name: a.config for a in artifacts}
        return [merge_json_object(target, {"mcpServers": servers})]

    def _write_text(self, target: Path, content: str) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def _write_json(self, target: Path, content: dict) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    def summarize_install(self, payload: InstallPayload) -> dict[str, int]:
        return {
            "skills": len(payload.skills) if self.supports_skills else 0,
            "rules": len(payload.rules) if self.supports_rules else 0,
            "commands": len(payload.commands) if self.supports_commands else 0,
            "mcp": len(payload.mcp) if self.supports_mcp else 0,
            "other": 0,
        }

    # -- YAML serializer --------------------------------

    def _dump_yaml(self, value: Any) -> str:
        return "\n".join(self._dump_yaml_lines(value, 0)).rstrip() + "\n"

    def _dump_yaml_lines(self, value: Any, indent: int) -> list[str]:
        prefix = " " * indent
        if isinstance(value, dict):
            lines: list[str] = []
            for key, item in value.items():
                scalar = self._yaml_scalar(item, indent)
                if scalar is not None:
                    lines.append(f"{prefix}{key}: {scalar}")
                else:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(self._dump_yaml_lines(item, indent + 2))
            return lines
        if isinstance(value, list):
            lines = []
            for item in value:
                scalar = self._yaml_scalar(item, indent)
                if scalar is not None:
                    lines.append(f"{prefix}- {scalar}")
                else:
                    nested = self._dump_yaml_lines(item, indent + 2)
                    if not nested:
                        lines.append(f"{prefix}-")
                    else:
                        first, rest = nested[0], nested[1:]
                        lines.append(f"{prefix}- {first.lstrip()}")
                        lines.extend(rest)
            return lines
        scalar = self._yaml_scalar(value, indent)
        return [f"{prefix}{scalar if scalar is not None else 'null'}"]

    def _yaml_scalar(self, value: Any, indent: int) -> Optional[str]:
        if isinstance(value, dict) or isinstance(value, list):
            return None
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value)
        if "\n" in text:
            block_indent = " " * (indent + 2)
            block_lines = text.rstrip("\n").splitlines() or [""]
            rendered = "\n".join(
                f"{block_indent}{line}" if line else block_indent for line in block_lines
            )
            return f"|\n{rendered}"
        safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:/@")
        if text and all(char in safe for char in text):
            return text
        return json.dumps(text)
