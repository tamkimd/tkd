from __future__ import annotations

from typing import Dict, Type

from tkd.adapters.antigravity import AntigravityAdapter
from tkd.adapters.base import AgentAdapter
from tkd.adapters.claude_code import ClaudeCodeAdapter
from tkd.adapters.codex import CodexAdapter
from tkd.adapters.continuedev import ContinueAdapter
from tkd.adapters.copilot import CopilotAdapter
from tkd.adapters.cursor import CursorAdapter
from tkd.adapters.gemini import GeminiAdapter
from tkd.adapters.kiro import KiroAdapter
from tkd.adapters.opencode import OpenCodeAdapter
from tkd.adapters.roo import RooAdapter
from tkd.adapters.trae import TraeAdapter
from tkd.adapters.windsurf import WindsurfAdapter

ADAPTER_REGISTRY: dict[str, type[AgentAdapter]] = {
    "antigravity": AntigravityAdapter,
    "codex": CodexAdapter,
    "claude-code": ClaudeCodeAdapter,
    "gemini": GeminiAdapter,
    "continue": ContinueAdapter,
    "cursor": CursorAdapter,
    "opencode": OpenCodeAdapter,
    "trae": TraeAdapter,
    "windsurf": WindsurfAdapter,
    "copilot": CopilotAdapter,
    "kiro": KiroAdapter,
    "roo": RooAdapter,
}

SUPPORTED_AGENTS = list(ADAPTER_REGISTRY)
WILDCARD_AGENTS = list(ADAPTER_REGISTRY)


def get_adapter(name: str) -> AgentAdapter:
    try:
        return ADAPTER_REGISTRY[name]()
    except KeyError as exc:
        raise ValueError(f"Unsupported agent: {name}") from exc
