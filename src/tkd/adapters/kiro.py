from __future__ import annotations

from tkd.adapters.base import AgentAdapter


class KiroAdapter(AgentAdapter):
    name = "kiro"
    config_dir = ".kiro"
    supports_mcp = True
