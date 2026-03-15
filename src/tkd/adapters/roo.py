from __future__ import annotations

from tkd.adapters.base import AgentAdapter


class RooAdapter(AgentAdapter):
    name = "roo"
    config_dir = ".roo"
    supports_mcp = True
