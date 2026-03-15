from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tkd.cli import cmd_check
from tkd.common.models import SourceConfig, TkdConfig
from tkd.config.load import load_config
from tests.conftest import Args, write


def test_only_json_config_supported(tmp_path: Path) -> None:
    write(tmp_path / "tkd.toml", "targets = { agents = '*' }\n")
    with pytest.raises(ValueError):
        asyncio.run(cmd_check(Args(str(tmp_path / "tkd.toml"))))


def test_load_config_returns_raw_tkd_json_shape(tmp_path: Path) -> None:
    write(
        tmp_path / "tkd.json",
        json.dumps(
            {
                "targets": {"agents": ["cursor"], "root": "."},
                "sources": {"local": "./registry"},
                "skills": {"local/skills": {"include": "all"}},
                "rules": {"local/rules": {"include": ["*"]}},
                "mcp": {"context7": {"command": "npx", "args": ["-y", "@upstash/context7"]}},
                "commands": {"local/commands": {"include": "all"}},
                "custom": {
                    "local/templates": {"include": ["*"], "scope": "root", "dest": ".github/"}
                },
            },
            indent=2,
        ),
    )

    config = load_config(tmp_path / "tkd.json")

    assert isinstance(config, TkdConfig)
    assert config.targets.root == "."
    assert config.sources == {
        "local": SourceConfig(
            name="local",
            type="local",
            path="./registry",
        )
    }
    assert config.skills["local/skills"].include == []
    assert config.skills["local/skills"].include_all is True
    assert config.rules["local/rules"].include == []
    assert config.rules["local/rules"].include_all is True
    assert "context7" in config.mcp
    assert config.commands["local/commands"].include == []
    assert config.commands["local/commands"].include_all is True
    assert "local/templates" in config.custom


@pytest.mark.asyncio
async def test_config_mutual_exclusion(tmp_path: Path) -> None:
    write(
        tmp_path / "tkd.json",
        json.dumps(
            {
                "targets": {"agents": ["cursor"], "root": "."},
                "sources": {"local": "./registry"},
                "skills": {
                    "local/skills": {
                        "include": ["core"],
                        "exclude": ["legacy"],
                    }
                },
            }
        ),
    )

    with pytest.raises(ValueError, match="include and exclude cannot be used at the same time"):
        await cmd_check(Args(str(tmp_path / "tkd.json")))


@pytest.mark.asyncio
async def test_config_default_inclusion(tmp_path: Path) -> None:
    write(
        tmp_path / "tkd.json",
        json.dumps(
            {
                "targets": {"agents": ["cursor"], "root": "."},
                "sources": {"local": "./registry"},
                "skills": {
                    "local/skills": {}  # Empty config should default to include: "*"
                },
            }
        ),
    )

    config = load_config(tmp_path / "tkd.json")
    assert config.skills["local/skills"].include_all is True
