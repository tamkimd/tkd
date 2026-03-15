from __future__ import annotations

from pathlib import Path

from tkd.adapters.base import AgentAdapter
from tkd.common.files import merge_json_object
from tkd.common.models import InstallPayload


class AntigravityAdapter(AgentAdapter):
    name = "antigravity"
    config_dir = ".agents"
    supports_mcp = True

    async def install(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        written = [
            workspace_root / self.config_dir / "skills" / skill.name for skill in payload.skills
        ]
        written.extend(
            self._layout_artifact_target(workspace_root, "rules", rule) for rule in payload.rules
        )
        written.extend(
            self._layout_artifact_target(workspace_root, "commands", command)
            for command in payload.commands
        )
        if payload.mcp:
            servers = {a.name: a.config for a in payload.mcp}
            written.append(
                merge_json_object(
                    target=self._mcp_target(workspace_root),
                    content={"mcpServers": servers},
                )
            )
        return written
