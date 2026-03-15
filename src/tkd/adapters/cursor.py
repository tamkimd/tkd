from __future__ import annotations

from pathlib import Path

from tkd.adapters.base import AgentAdapter
from tkd.common.models import InstallPayload


class CursorAdapter(AgentAdapter):
    name = "cursor"
    config_dir = ".cursor"
    supports_mcp = True

    def _do_install_rules(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        written: list[Path] = []
        for rule in payload.rules:
            body = f"---\ndescription: {rule.name}\nalwaysApply: true\n---\n\n{rule.content}\n"
            written.append(
                self._write_text(
                    target=self._layout_artifact_target(workspace_root, "rules", rule),
                    content=body,
                )
            )
        return written
