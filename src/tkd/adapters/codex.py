from __future__ import annotations

import json
from pathlib import Path

from tkd.adapters.base import AgentAdapter
from tkd.common.files import mirror_path
from tkd.common.models import InstallPayload
from tkd.common.workspace import shared_agents_root


class CodexAdapter(AgentAdapter):
    name = "codex"
    config_dir = ".codex"
    supports_mcp = True

    async def install(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        shared = shared_agents_root(workspace_root)
        written: list[Path] = []

        for skill in payload.skills:
            written.append(shared / "skills" / skill.name)

        if payload.rules:
            content = "\n\n".join(rule.content for rule in payload.rules)
            written.append(
                self._write_text(
                    target=self._rules_document_target(workspace_root),
                    content=content + "\n",
                )
            )

        for command in payload.commands:
            source = shared / "workflows" / f"{command.name}.md"
            dest = self._layout_artifact_target(workspace_root, "commands", command)
            written.append(mirror_path(source, dest))

        if payload.mcp:
            servers = {}
            for artifact in payload.mcp:
                config = dict(artifact.config)
                if config.get("type") == "streamable-http":
                    config.pop("type")
                headers = config.pop("headers", None)
                if headers:
                    config["http_headers"] = headers
                servers[artifact.name] = config
            written.append(
                self._write_text(
                    target=self._mcp_target(workspace_root),
                    content=self._render_codex_toml(servers),
                )
            )
        return written

    def _render_codex_toml(self, servers: dict[str, dict]) -> str:
        lines: list[str] = []
        for name, config in servers.items():
            lines.append(f"[mcp_servers.{name}]")
            for key, value in config.items():
                if isinstance(value, str):
                    lines.append(f'{key} = "{value}"')
                elif isinstance(value, bool):
                    lines.append(f"{key} = {'true' if value else 'false'}")
                elif isinstance(value, list):
                    rendered = ", ".join(f'"{item}"' for item in value)
                    lines.append(f"{key} = [{rendered}]")
                elif isinstance(value, dict):
                    inline = ", ".join(f'"{k}" = "{v}"' for k, v in value.items())
                    lines.append(f"{key} = {{ {inline} }}")
                else:
                    lines.append(f"{key} = {json.dumps(value)}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"
