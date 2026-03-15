from __future__ import annotations

from pathlib import Path

from tkd.common.models import ResolvedSource, SourceConfig
from tkd.registry.git_resolver import GitResolver
from tkd.registry.local_resolver import LocalResolver


async def resolve_source(
    source: SourceConfig,
    base_dir: Path,
    cache_dir: Path,
    refresh: bool = False,
) -> ResolvedSource:
    if source.type == "local":
        return await LocalResolver().resolve(source, base_dir)
    if source.type == "git":
        return await GitResolver(cache_dir, refresh=refresh).resolve(source, base_dir)
    raise ValueError(f"Unsupported source type: {source.type}")
