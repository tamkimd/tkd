from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

from tkd.common.models import ResolvedSource, SourceConfig
from tkd.registry.resolver_base import Resolver


class GitResolver(Resolver):
    def __init__(self, cache_dir: Path, refresh: bool = False, timeout_seconds: int = 30) -> None:
        self.cache_dir = cache_dir
        self.refresh = refresh
        self.timeout_seconds = timeout_seconds

    def _git_command(self, source: SourceConfig, *args: str) -> list[str]:
        command = ["git"]
        if source.auth:
            if source.auth.type == "bearer" and source.auth.token:
                header = "http.extraHeader=Authorization: Bearer {0}".format(source.auth.token)
                command.extend(["-c", header])
            elif source.auth.type == "header" and source.auth.name and source.auth.value:
                header = "http.extraHeader={0}: {1}".format(source.auth.name, source.auth.value)
                command.extend(["-c", header])
        command.extend(args)
        return command

    def _run_git(
        self,
        source: SourceConfig,
        cwd: Path,
        *args: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            self._git_command(source, *args),
            check=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.timeout_seconds,
        )

    def _remote_url(self, target: Path) -> str:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            check=True,
            cwd=target,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.timeout_seconds,
        )
        return result.stdout.strip()

    async def resolve(self, source: SourceConfig, base_dir: Path) -> ResolvedSource:
        if not source.url:
            raise ValueError(f"Git source {source.name} requires url")
        ref = source.ref or "HEAD"
        target = self.cache_dir / source.name
        if not target.exists():
            clone_args = ["clone", "--depth", "1"]
            if ref != "HEAD":
                clone_args.extend(["--branch", ref, "--single-branch"])
            clone_args.extend([source.url, str(target)])
            await asyncio.to_thread(self._run_git, source, base_dir, *clone_args)
        else:
            if not (target / ".git").exists():
                await asyncio.to_thread(shutil.rmtree, target)
                clone_args = ["clone", "--depth", "1"]
                if ref != "HEAD":
                    clone_args.extend(["--branch", ref, "--single-branch"])
                clone_args.extend([source.url, str(target)])
                await asyncio.to_thread(self._run_git, source, base_dir, *clone_args)
                if ref == "HEAD":
                    return ResolvedSource(config=source, root=target)
                await asyncio.to_thread(self._run_git, source, target, "checkout", "--force", ref)
                return ResolvedSource(config=source, root=target)
            try:
                remote_url = await asyncio.to_thread(self._remote_url, target)
            except subprocess.SubprocessError:
                remote_url = ""
            if remote_url and remote_url != source.url:
                await asyncio.to_thread(shutil.rmtree, target)
                return await self.resolve(source, base_dir)
            if not self.refresh:
                return ResolvedSource(config=source, root=target)
            fetch_args = ["fetch", "--depth", "1", "origin"]
            if ref != "HEAD":
                fetch_args.append(ref)
            try:
                await asyncio.to_thread(self._run_git, source, target, *fetch_args)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                return ResolvedSource(config=source, root=target)
        if ref != "HEAD":
            try:
                await asyncio.to_thread(self._run_git, source, target, "checkout", "--force", ref)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                return ResolvedSource(config=source, root=target)
        return ResolvedSource(config=source, root=target)
