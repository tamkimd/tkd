from __future__ import annotations

from tkd.adapters import AGENT_LAYOUTS


def test_all_supported_agents_have_declared_layouts() -> None:
    expected = {
        "antigravity",
        "codex",
        "claude-code",
        "gemini",
        "continue",
        "cursor",
        "opencode",
        "trae",
        "windsurf",
        "copilot",
        "kiro",
        "roo",
    }
    assert set(AGENT_LAYOUTS) == expected
