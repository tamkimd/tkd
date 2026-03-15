from __future__ import annotations

import asyncio
import os
import re
from argparse import ArgumentParser
from collections import OrderedDict
from functools import reduce
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tkd.adapters import get_adapter
from tkd.artifacts.command import load_command
from tkd.artifacts.rule import load_rule
from tkd.artifacts.skill import load_skill
from tkd.common import EnvMap, build_shared_agents_layer, copy_path, shared_agents_root
from tkd.common.models import (
    CustomConfig,
    InstallPayload,
    MCPArtifact,
    SourceConfig,
    TkdConfig,
)
from tkd.config.load import load_config
from tkd.config.parse import (
    iter_collections,
    iter_command_collections,
    iter_custom_configs,
    iter_named_commands,
    selection_names,
    target_agents,
    target_root,
)
from tkd.registry import resolve_source

DEFAULT_CONFIG = """{
  "targets": {
    "agents": "*",
    "root": "."
  },
  "sources": {
    "local": {
      "path": "./registry"
    }
  },
  "skills": {
    "local/skills": {
      "include": "all"
    }
  },
  "rules": {
    "local/rules": {
      "include": []
    }
  },
  "mcp": {},
  "commands": {},
  "custom": {}
}
"""

CONSOLE = Console()
_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _config_path(explicit: Optional[str]) -> Path:
    if explicit:
        path = Path(explicit).resolve()
        if path.suffix != ".json":
            raise ValueError("Only JSON config is supported. Use a .json file.")
        return path
    return Path("tkd.json").resolve()


def _dedupe(items, key):
    ordered = OrderedDict()
    for item in items:
        ordered[key(item)] = item
    return list(ordered.values())


def _load_dotenv(path: Path) -> EnvMap:
    if not path.exists():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def _parse_env_flags(values: Optional[list[str]]) -> EnvMap:
    env = {}
    for item in values or []:
        if "=" not in item:
            raise ValueError("Invalid --env value: {0}".format(item))
        key, value = item.split("=", 1)
        env[key] = value
    return env


def _build_env_provider(config_path: Path, cli_env: EnvMap):
    dotenv_values = _load_dotenv(config_path.parent / ".env")
    prompted = {}  # type: EnvMap

    def has_value(mapping: EnvMap, name: str) -> bool:
        return name in mapping and mapping[name] != ""

    def resolve(name: str, prompt_missing: bool) -> str:
        if has_value(cli_env, name):
            return cli_env[name]
        if has_value(os.environ, name):
            return os.environ[name]
        if has_value(dotenv_values, name):
            return dotenv_values[name]
        if has_value(prompted, name):
            return prompted[name]
        if prompt_missing:
            prompt = "[bold yellow]Enter value for {0}:[/bold yellow] ".format(name)
            prompted[name] = CONSOLE.input(prompt)
            return prompted[name]
        raise ValueError(
            "Missing environment variable: {0}. Provide it with --env {0}=..., "
            "export it in your shell, or add it to .env.".format(name)
        )

    return resolve


def _available_env_values(config_path: Path, cli_env: EnvMap) -> EnvMap:
    values = dict(_load_dotenv(config_path.parent / ".env"))
    values.update(os.environ)
    values.update(cli_env)
    return values


def _collect_env_placeholders(value, found):
    if isinstance(value, str):
        found.update(_ENV_PATTERN.findall(value))
        return
    if isinstance(value, list):
        for item in value:
            _collect_env_placeholders(item, found)
        return
    if isinstance(value, dict):
        for item in value.values():
            _collect_env_placeholders(item, found)


def _required_env_names(config: TkdConfig):
    names = set()
    for source in config.sources.values():
        _collect_env_placeholders(source.path, names)
        _collect_env_placeholders(source.url, names)
        _collect_env_placeholders(source.ref, names)
        if source.auth:
            _collect_env_placeholders(source.auth.token, names)
            _collect_env_placeholders(source.auth.name, names)
            _collect_env_placeholders(source.auth.value, names)
    for entry in config.mcp.values():
        _collect_env_placeholders(entry, names)
    return sorted(names)


def _missing_env_names(config_path: Path, cli_env: EnvMap, config: TkdConfig):
    available = _available_env_values(config_path, cli_env)
    return [name for name in _required_env_names(config) if available.get(name, "") == ""]


def _raise_missing_env_error(missing):
    joined = ", ".join(missing)
    message = (
        "Missing required environment variables: {0}\n"
        "Provide them with `--env KEY=VALUE`, export them in your shell, or add them to `.env`."
    )
    raise ValueError(message.format(joined))


def _prompt_for_missing_envs(missing, cli_env: EnvMap) -> EnvMap:
    prompted_env = dict(cli_env)
    for name in missing:
        prompt = "[bold yellow]Enter value for {0}:[/bold yellow] ".format(name)
        prompted_env[name] = CONSOLE.input(prompt)
    return prompted_env


def _resolve_env_placeholders(value, resolver, prompt_missing: bool, require_env: bool):
    if isinstance(value, str):

        def replace_match(match):
            try:
                return resolver(match.group(1), prompt_missing)
            except ValueError:
                if require_env:
                    raise
                return match.group(0)

        return _ENV_PATTERN.sub(replace_match, value)
    if isinstance(value, list):
        return [
            _resolve_env_placeholders(item, resolver, prompt_missing, require_env) for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _resolve_env_placeholders(item, resolver, prompt_missing, require_env)
            for key, item in value.items()
        }
    return value


def _resolve_source_config(
    source: SourceConfig,
    resolver,
    prompt_missing: bool,
    require_env: bool,
) -> SourceConfig:
    auth = source.auth
    if auth:
        auth = auth.model_copy(
            update={
                "token": _resolve_env_placeholders(
                    auth.token,
                    resolver,
                    prompt_missing,
                    require_env,
                ),
                "name": _resolve_env_placeholders(
                    auth.name,
                    resolver,
                    prompt_missing,
                    require_env,
                ),
                "value": _resolve_env_placeholders(
                    auth.value,
                    resolver,
                    prompt_missing,
                    require_env,
                ),
            }
        )
    return source.model_copy(
        update={
            "path": _resolve_env_placeholders(
                source.path,
                resolver,
                prompt_missing,
                require_env,
            ),
            "url": _resolve_env_placeholders(
                source.url,
                resolver,
                prompt_missing,
                require_env,
            ),
            "ref": _resolve_env_placeholders(
                source.ref,
                resolver,
                prompt_missing,
                require_env,
            ),
            "auth": auth,
        }
    )


async def _resolve_config(
    config_path: Path,
    cli_env: EnvMap,
    prompt_missing: bool,
    require_env: bool,
):
    config = load_config(config_path)
    env_resolver = _build_env_provider(config_path, cli_env)
    sources = {
        source.name: _resolve_source_config(source, env_resolver, prompt_missing, require_env)
        for source in config.sources.values()
    }
    return config, sources, env_resolver


async def _resolve_selected_sources(
    config_path: Path,
    names,
    cli_env,
    prompt_missing,
    require_env,
    refresh: bool = False,
):
    config, raw_sources, env_resolver = await _resolve_config(
        config_path,
        cli_env,
        prompt_missing,
        require_env,
    )
    cache_dir = config_path.parent / ".tkd-cache"
    cache_dir.mkdir(exist_ok=True)

    async def resolve_one(name):
        return name, await resolve_source(raw_sources[name], config_path.parent, cache_dir, refresh)

    ordered_names = sorted(names)
    tasks = [asyncio.create_task(resolve_one(name)) for name in ordered_names]
    resolved_pairs = []
    total = len(tasks)
    for index, task in enumerate(asyncio.as_completed(tasks), start=1):
        name, resolved = await task
        resolved_pairs.append((name, resolved))
        CONSOLE.print("[dim]Resolved source {0}/{1}: {2}[/dim]".format(index, total, name))
    return config, dict(resolved_pairs), env_resolver


def _collect_skill_names(source):
    base = source.root / "skills"
    if not base.exists():
        return []
    return sorted(
        entry.name for entry in base.iterdir() if entry.is_dir() and (entry / "SKILL.md").exists()
    )


def _collect_rule_names(source):
    base = source.root / "rules"
    if not base.exists():
        return []
    names = []
    for entry in base.iterdir():
        if entry.is_dir() and (entry / "RULE.md").exists():
            names.append(entry.name)
        elif entry.is_file() and entry.suffix in {".md", ".mdc"}:
            names.append(entry.name)
    return sorted(names)


def _collect_command_names(source):
    base = source.root / "commands"
    if not base.exists():
        return []
    return sorted(
        entry.stem
        for entry in base.iterdir()
        if entry.is_file() and entry.suffix in {".md", ".markdown"}
    )


def _collect_custom_entries(source, artifact: str):
    base = source.root / artifact
    if not base.exists():
        return []
    return sorted(entry.name for entry in base.iterdir())


async def _build_payload(
    config_path: Path,
    cli_env: Optional[EnvMap] = None,
    prompt_missing: bool = False,
    require_env: bool = False,
    refresh: bool = False,
):
    cli_env = cli_env or {}
    loaded_config = load_config(config_path)
    source_groups = [
        {source for source, _ in iter_collections(loaded_config.skills, "skills")},
        {source for source, _ in iter_collections(loaded_config.rules, "rules")},
        {source for _, source in iter_named_commands(loaded_config)},
        {source for source, _ in iter_command_collections(loaded_config)},
        {source for source, _, _ in iter_custom_configs(loaded_config)},
    ]
    required_sources = reduce(lambda left, right: left.union(right), source_groups, set())
    config, sources, env_resolver = await _resolve_selected_sources(
        config_path,
        required_sources,
        cli_env,
        prompt_missing,
        require_env,
        refresh,
    )
    payload = InstallPayload()

    for source_name, collection in iter_collections(config.skills, "skills"):
        if not collection.enabled:
            continue
        names = selection_names(
            _collect_skill_names(sources[source_name]),
            collection.include,
            collection.exclude,
            collection.include_all,
        )
        for name in names:
            payload.skills.append(load_skill(sources[source_name].skill_path(name)))

    for source_name, collection in iter_collections(config.rules, "rules"):
        if not collection.enabled:
            continue
        names = selection_names(
            _collect_rule_names(sources[source_name]),
            collection.include,
            collection.exclude,
            collection.include_all,
        )
        for name in names:
            payload.rules.append(load_rule(sources[source_name].rule_path(name)))

    for command_name, source_name in iter_named_commands(config):
        payload.commands.append(load_command(sources[source_name].command_path(command_name)))

    for source_name, collection in iter_command_collections(config):
        if not collection.enabled:
            continue
        names = selection_names(
            _collect_command_names(sources[source_name]),
            collection.include,
            collection.exclude,
            collection.include_all,
        )
        for name in names:
            payload.commands.append(load_command(sources[source_name].command_path(name)))

    for name, value in config.mcp.items():
        payload.mcp.append(
            MCPArtifact(
                name=name,
                config=_resolve_env_placeholders(value, env_resolver, prompt_missing, require_env),
                path=config_path,
            )
        )

    payload.skills = _dedupe(payload.skills, lambda item: item.name)
    payload.rules = _dedupe(payload.rules, lambda item: item.name)
    payload.mcp = _dedupe(payload.mcp, lambda item: item.name)
    payload.commands = _dedupe(payload.commands, lambda item: item.name)
    return config, sources, payload


async def _copy_path(source_path: Path, dest_path: Path):
    def do_copy():
        return copy_path(source_path, dest_path)

    return await asyncio.to_thread(do_copy)


async def _sync_shared_agent_layer(payload: InstallPayload, workspace_root: Path):
    return await asyncio.to_thread(build_shared_agents_layer, payload, workspace_root)


def _agent_scope_destinations(workspace_root: Path, agents, dest):
    destinations = [shared_agents_root(workspace_root) / dest]
    for name in agents:
        adapter = get_adapter(name)
        destinations.append(adapter.config_root(workspace_root) / dest)
    deduped = []
    seen = set()
    for destination in destinations:
        key = str(destination)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(destination)
    return deduped


def _resolve_custom_destinations(
    workspace_root: Path,
    agents,
    custom: CustomConfig,
    item_name: str,
):
    raw_dest = custom.dest or ""
    is_directory_dest = raw_dest.endswith("/") or raw_dest.endswith("\\")
    if custom.scope == "root":
        base = workspace_root
        target = base / raw_dest if raw_dest else base / item_name
        return [target / item_name if is_directory_dest else target]
    if custom.scope == "agents":
        targets = _agent_scope_destinations(workspace_root, agents, raw_dest)
        return [
            target / item_name if is_directory_dest or not raw_dest else target
            for target in targets
        ]
    raise ValueError("Unsupported custom scope: {0}".format(custom.scope))


async def _sync_custom(config: TkdConfig, sources, workspace_root: Path):
    written = []
    tasks = []
    for source_name, artifact, custom in iter_custom_configs(config):
        if not custom.enabled:
            continue
        available = _collect_custom_entries(sources[source_name], artifact)
        names = selection_names(available, custom.include, custom.exclude, custom.include_all)
        for name in names:
            source_path = sources[source_name].root / artifact / name
            destinations = _resolve_custom_destinations(
                workspace_root,
                target_agents(config),
                custom,
                name,
            )
            for destination in destinations:
                tasks.append(_copy_path(source_path, destination))
    if tasks:
        written.extend(await asyncio.gather(*tasks))
    return written


def _render_summary(title: str, summary: dict[str, list[str]]):
    table = Table(title=title)
    table.add_column("Kind", style="cyan", no_wrap=True)
    table.add_column("Count", style="magenta", justify="right", no_wrap=True)
    table.add_column("Details", style="white")
    for key, values in summary.items():
        rendered = "\n".join(values) if values else "-"
        table.add_row(key, str(len(values)), rendered)
    CONSOLE.print(table)


def _render_sync_paths(workspace_root: Path, values):
    rendered = []
    for item in values:
        path = Path(item)
        try:
            rendered.append(str(path.relative_to(workspace_root)))
        except ValueError:
            rendered.append(str(path))
    return rendered


def _classify_sync_entry(relative_path: str) -> str:
    path = Path(relative_path)
    parts = set(path.parts)
    name = path.name.lower()
    if "mcpservers" in parts or name.endswith("mcp.json") or name == "mcp.json":
        return "mcp"
    if "commands" in parts or "workflows" in parts or "prompts" in parts:
        return "commands"
    if "skills" in parts:
        return "skills"
    if "rules" in parts or "steering" in parts or "rules-general" in parts:
        return "rules"
    if name in {"agents.md", "claude.md", "gemini.md", "copilot-instructions.md"}:
        return "rules"
    return "other"


def _render_sync_summary(
    workspace_root: Path,
    written: dict[str, list[str]],
    payload: InstallPayload,
):
    summary = Table(title="Sync Complete")
    summary.add_column("Target", style="cyan", no_wrap=True)
    summary.add_column("Skills", justify="right", style="magenta")
    summary.add_column("Rules", justify="right", style="magenta")
    summary.add_column("Commands", justify="right", style="magenta")
    summary.add_column("MCP", justify="right", style="magenta")
    summary.add_column("Other", justify="right", style="magenta")

    custom_paths = written.get("custom", [])
    for key, values in written.items():
        if key in {"custom", "shared"}:
            continue
        counts = get_adapter(key).summarize_install(payload)
        summary.add_row(
            key,
            str(counts["skills"]),
            str(counts["rules"]),
            str(counts["commands"]),
            str(counts["mcp"]),
            str(counts["other"]),
        )
    CONSOLE.print(summary)

    if custom_paths:
        custom_table = Table(title="Custom Outputs")
        custom_table.add_column("Path", style="white")
        for item in _render_sync_paths(workspace_root, custom_paths):
            custom_table.add_row(item)
        CONSOLE.print(custom_table)


async def cmd_init(args) -> int:
    config_path = _config_path(args.config)
    if config_path.exists() and not args.force:
        raise SystemExit("{0} already exists; use --force to overwrite".format(config_path))
    config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    CONSOLE.print(Panel.fit(str(config_path), title="Created Config", border_style="green"))
    return 0


async def _cmd_check(args, title: str = "Planned Install", show_workspace: bool = True) -> int:
    config_path = _config_path(args.config)
    cli_env = _parse_env_flags(args.env)
    with CONSOLE.status("[bold blue]Validating config and artifacts...[/bold blue]"):
        config, sources, payload = await _build_payload(
            config_path,
            cli_env,
            False,
            False,
            getattr(args, "refresh", False),
        )
    custom_summary = []
    for source_name, artifact, custom in iter_custom_configs(config):
        available = _collect_custom_entries(sources[source_name], artifact)
        custom_summary.extend(
            selection_names(
                available,
                custom.include,
                custom.exclude,
                custom.include_all,
            )
        )
    _render_summary(
        title,
        {
            "agents": target_agents(config),
            "skills": [skill.name for skill in payload.skills],
            "rules": [rule.name for rule in payload.rules],
            "mcp": [mcp.name for mcp in payload.mcp],
            "commands": [command.name for command in payload.commands],
            "custom": custom_summary,
        },
    )
    if show_workspace:
        CONSOLE.print("[bold]Workspace:[/bold] {0}".format(target_root(config_path, config)))
    return 0


async def cmd_check(args) -> int:
    return await _cmd_check(args)


async def cmd_sync(args) -> int:
    config_path = _config_path(args.config)
    cli_env = _parse_env_flags(args.env)
    loaded_config = load_config(config_path)
    missing = _missing_env_names(config_path, cli_env, loaded_config)
    if missing:
        if getattr(args, "ask_env", False):
            cli_env = _prompt_for_missing_envs(missing, cli_env)
        else:
            _raise_missing_env_error(missing)
    with CONSOLE.status("[bold blue]Resolving sources and preparing payload...[/bold blue]"):
        config, sources, payload = await _build_payload(
            config_path,
            cli_env,
            getattr(args, "ask_env", False),
            True,
            getattr(args, "refresh", False),
        )
    workspace_root = target_root(config_path, config)
    active_agents = target_agents(config)

    async def install_for_agent(name):
        adapter = get_adapter(name)
        paths = await adapter.install(payload, workspace_root)
        return name, [str(path) for path in paths]

    with CONSOLE.status("[bold blue]Installing agent artifacts...[/bold blue]"):
        await _sync_shared_agent_layer(payload, workspace_root)
        installed = await asyncio.gather(*(install_for_agent(name) for name in active_agents))
        custom_paths = await _sync_custom(config, sources, workspace_root)

    written = dict(installed)
    if custom_paths:
        written["custom"] = [str(path) for path in custom_paths]

    _render_sync_summary(workspace_root, written, payload)
    return 0


def _find_subparser(parser: ArgumentParser, name: str):
    for action in getattr(parser, "_actions", []):
        choices = getattr(action, "choices", None)
        if choices and name in choices:
            return choices[name]
    return None


async def cmd_help(args) -> int:
    parser = args.parser
    topic = getattr(args, "topic", None)
    if not topic:
        parser.print_help()
        return 0
    subparser = _find_subparser(parser, topic)
    if subparser is None:
        raise SystemExit("Unknown command: {0}".format(topic))
    subparser.print_help()
    return 0


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="tkd",
        description="Distribute skills, rules, commands, MCP configs, and custom files "
        "into agent-native workspace layouts.",
    )
    parser.set_defaults(parser=parser)
    parser.add_argument("--config")
    parser.add_argument("--env", action="append")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh cached git sources before building the payload",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a starter tkd.json")
    init_parser.add_argument("--config")
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(func=cmd_init)

    check_parser = subparsers.add_parser("check", help="Resolve config and show the install plan")
    check_parser.add_argument("--config")
    check_parser.add_argument("--env", action="append")
    check_parser.add_argument("--refresh", action="store_true")
    check_parser.set_defaults(func=cmd_check)

    sync_parser = subparsers.add_parser("sync", help="Write resolved artifacts into the workspace")
    sync_parser.add_argument("--config")
    sync_parser.add_argument("--env", action="append")
    sync_parser.add_argument("--refresh", action="store_true")
    sync_parser.add_argument(
        "--ask-env",
        "--prompt-missing-env",
        dest="ask_env",
        action="store_true",
        help="Prompt for missing environment variables instead of failing fast",
    )
    sync_parser.set_defaults(func=cmd_sync)

    help_parser = subparsers.add_parser("help", help="Show CLI help or command help")
    help_parser.add_argument("topic", nargs="?")
    help_parser.set_defaults(func=cmd_help)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return asyncio.run(args.func(args))
    except ValueError as exc:
        CONSOLE.print(Panel.fit(str(exc), title="Error", border_style="red"))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
