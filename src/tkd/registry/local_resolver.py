from __future__ import annotations

import asyncio
from pathlib import Path

from tkd.common.models import ResolvedSource, SourceConfig
from tkd.registry.resolver_base import Resolver


class LocalResolver(Resolver):
    async def resolve(self, source: SourceConfig, base_dir: Path) -> ResolvedSource:
        if not source.path:
            raise ValueError(f"Local source {source.name} requires path")
        root = await asyncio.to_thread(lambda: (base_dir / source.path).resolve())
        if not root.exists():
            raise ValueError(f"Local source path does not exist: {root}")
        return ResolvedSource(config=source, root=root)
