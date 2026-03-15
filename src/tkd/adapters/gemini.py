from __future__ import annotations

from pathlib import Path

from tkd.adapters.base import AgentAdapter
from tkd.common.models import InstallPayload


class GeminiAdapter(AgentAdapter):
    name = "gemini"
    config_dir = ".gemini"
    supports_mcp = True

    def _do_install_rules(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        return self._write_joined_rules_doc(
            target=self._rules_document_target(workspace_root),
            rules=payload.rules,
        )

    def _do_install_commands(self, payload: InstallPayload, workspace_root: Path) -> list[Path]:
        command_root = self._commands_container(workspace_root)
        written: list[Path] = []
        for command in payload.commands:
            prompt = command.template.replace('"""', '\\"\\"\\"')
            content = f'description = "{command.description}"\nprompt = """\n{prompt}\n"""\n'
            written.append(
                self._write_text(
                    target=command_root / f"{command.name}.toml",
                    content=content,
                )
            )
        return written
