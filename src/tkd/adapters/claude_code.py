from __future__ import annotations

from pathlib import Path

from tkd.adapters.base import AgentAdapter
from tkd.common.models import InstallPayload


class ClaudeCodeAdapter(AgentAdapter):
    name = "claude-code"
    config_dir = ".claude"
    supports_mcp = True

    def _do_install_rules(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        return self._write_joined_rules_doc(
            target=self._rules_document_target(workspace_root),
            rules=payload.rules,
        )

    def _do_install_commands(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        return self._write_frontmatter_commands(
            workspace_root=workspace_root,
            commands=payload.commands,
        )
