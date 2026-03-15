from __future__ import annotations

from pathlib import Path

from tkd.adapters.base import AgentAdapter
from tkd.common.models import InstallPayload


class CopilotAdapter(AgentAdapter):
    name = "copilot"
    config_dir = ".github"
    supports_mcp = True

    def _do_install_rules(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        return self._write_joined_rules_doc(
            target=self._rules_document_target(workspace_root),
            rules=payload.rules,
        )
