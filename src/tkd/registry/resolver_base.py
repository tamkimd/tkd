from __future__ import annotations

from pathlib import Path

from tkd.common.models import ResolvedSource, SourceConfig


class Resolver:
    async def resolve(self, source: SourceConfig, base_dir: Path) -> ResolvedSource:
        raise NotImplementedError
