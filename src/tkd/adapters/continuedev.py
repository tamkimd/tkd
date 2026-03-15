from __future__ import annotations

from pathlib import Path

from tkd.adapters.base import AgentAdapter
from tkd.common.models import InstallPayload


class ContinueAdapter(AgentAdapter):
    name = "continue"
    config_dir = ".continue"
    supports_skills = True
    supports_mcp = True

    async def install(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        written = self._install_shared_artifacts(workspace_root, "skills", payload.skills)
        config = {
            "name": "tkd-generated",
            "version": "1.0.0",
            "schema": "v1",
            "context": [
                {"provider": "diff"},
                {"provider": "file"},
                {"provider": "code"},
                {"provider": "terminal"},
            ],
        }
        if payload.rules:
            config["rules"] = [rule.content for rule in payload.rules]
        if payload.commands:
            config["prompts"] = [
                {
                    "name": command.name,
                    "description": command.description,
                    "prompt": command.template.strip(),
                }
                for command in payload.commands
            ]
        if payload.mcp:
            config["mcpServers"] = []
            for artifact in payload.mcp:
                server = dict(artifact.config)
                server.setdefault("name", artifact.name)
                config["mcpServers"].append(server)
        written.append(
            self._write_continue_config(
                target=self._mcp_target(workspace_root),
                content=config,
            )
        )
        return written

    def _write_continue_config(self, target: Path, content: dict) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self._dump_yaml(content), encoding="utf-8")
        return target
