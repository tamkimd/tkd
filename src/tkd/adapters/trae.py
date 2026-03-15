from __future__ import annotations

from tkd.adapters.base import AgentAdapter


class TraeAdapter(AgentAdapter):
    name = "trae"
    config_dir = ".trae"
    supports_mcp = True
