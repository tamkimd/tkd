from __future__ import annotations

from pathlib import Path

from tkd.adapters.base import AgentAdapter
from tkd.common.models import InstallPayload


class WindsurfAdapter(AgentAdapter):
    name = "windsurf"
    config_dir = ".windsurf"
    supports_mcp = True

    def _do_install_rules(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        written: list[Path] = []
        for rule in payload.rules:
            body = f"---\ntrigger: always_on\n---\n\n{rule.content.strip()}\n"
            written.append(
                self._write_text(
                    target=self._layout_artifact_target(workspace_root, "rules", rule),
                    content=body,
                )
            )
        return written

    def _do_install_mcp(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        return self._merge_json_mcp_servers(
            target=self._mcp_target(workspace_root),
            artifacts=payload.mcp,
        )
