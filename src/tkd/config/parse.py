from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator, Tuple

from tkd.adapters import SUPPORTED_AGENTS, WILDCARD_AGENTS
from tkd.common.models import CollectionConfig, CommandConfig, CustomConfig, TkdConfig


def parse_selector(selector: str) -> tuple[str, str]:
    parts = selector.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError("Invalid selector: {0}".format(selector))
    return parts[0], parts[1]


def expand_agents(raw_agents) -> list[str]:
    legacy_aliases = {"gemini-cli": "gemini"}
    if raw_agents == "*" or raw_agents == ["*"]:
        return list(WILDCARD_AGENTS)
    agents = [legacy_aliases.get(agent, agent) for agent in list(raw_agents)]
    if "*" in agents:
        return list(WILDCARD_AGENTS)
    invalid = [agent for agent in agents if agent not in SUPPORTED_AGENTS]
    if invalid:
        raise ValueError("Unsupported agents: {0}".format(", ".join(invalid)))
    return agents


def target_agents(config: TkdConfig) -> list[str]:
    agents = expand_agents(config.targets.agents)
    if not agents:
        raise ValueError("Config must define at least one target agent")
    return agents


def target_root(config_path: Path, config: TkdConfig) -> Path:
    return (config_path.parent / config.targets.root).resolve()


def selection_names(
    available: Iterable[str],
    include: list[str],
    exclude: list[str],
    include_all: bool,
) -> list[str]:
    selected = list(available) if include_all or not include else include
    blocked = set(exclude)
    return [name for name in selected if name not in blocked]


def resolve_collection_source(
    selector: str,
    source_override: str,
    expected_artifact: str,
) -> tuple[str, str]:
    source, artifact = parse_selector(source_override or selector)
    if artifact != expected_artifact:
        raise ValueError(
            "{0} selector must reference {1}: {2}".format(
                expected_artifact.capitalize(),
                expected_artifact,
                source_override or selector,
            )
        )
    return source, artifact


def iter_collections(
    section: dict[str, CollectionConfig],
    expected_artifact: str,
) -> Iterator[tuple[str, CollectionConfig]]:
    for selector, config in section.items():
        source, _ = resolve_collection_source(selector, config.source or "", expected_artifact)
        yield source, config


def iter_command_collections(config: TkdConfig) -> Iterator[tuple[str, CommandConfig]]:
    for selector, entry in config.commands.items():
        if "/" not in selector:
            continue
        source, _ = resolve_collection_source(selector, entry.source or "", "commands")
        yield source, entry


def iter_named_commands(config: TkdConfig) -> Iterator[tuple[str, str]]:
    for name, entry in config.commands.items():
        if "/" in name:
            continue
        if not entry.source:
            raise ValueError("Command {0} must define a source selector".format(name))
        source, _ = resolve_collection_source(name, entry.source, "commands")
        yield name, source


def iter_custom_configs(config: TkdConfig) -> Iterator[tuple[str, str, CustomConfig]]:
    for selector, entry in config.custom.items():
        _, expected_artifact = parse_selector(selector)
        source, artifact = resolve_collection_source(
            selector,
            entry.source or "",
            expected_artifact,
        )
        yield source, artifact, entry
