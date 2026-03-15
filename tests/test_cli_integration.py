from __future__ import annotations

import json
from pathlib import Path

import pytest

from tkd.cli import cmd_check, cmd_sync
from tests.conftest import Args, write


@pytest.mark.asyncio
async def test_validate_and_sync(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    write(
        tmp_path / "registry" / "skills" / "example-skill" / "SKILL.md",
        "---\nname: example-skill\ndescription: Example skill for tests\n---\n\nUse this skill.\n",
    )
    write(tmp_path / "registry" / "rules" / "org" / "RULE.md", "Always write tests.\n")
    write(
        tmp_path / "registry" / "mcp" / "github" / "mcp.json", '{"url":"https://example.com/mcp"}'
    )
    write(
        tmp_path / "registry" / "commands" / "review.md",
        (
            "---\n"
            "description: Review current changes\n"
            "---\n\n"
            "Review the current diff and suggest fixes.\n"
        ),
    )
    write(
        tmp_path / "tkd.json",
        json.dumps(
            {
                "targets": {"agents": ["codex", "claude-code"], "root": "."},
                "sources": {
                    "workspace": {
                        "path": "./registry",
                    }
                },
                "skills": {"workspace/skills": {"include": ["example-skill"]}},
                "rules": {"workspace/rules": {"include": ["org"]}},
                "mcp": {},
                "commands": {"review": "workspace/commands/"},
                "custom": {},
            },
            indent=2,
        ),
    )

    assert await cmd_check(Args(str(tmp_path / "tkd.json"))) == 0
    assert await cmd_sync(Args(str(tmp_path / "tkd.json"))) == 0

    assert (tmp_path / ".agents" / "skills" / "example-skill" / "SKILL.md").exists()
    assert (tmp_path / ".claude" / "skills" / "example-skill" / "SKILL.md").exists()
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    codex_prompt = tmp_path / "home" / ".codex" / "prompts" / "review.md"
    assert codex_prompt.exists()
    assert (tmp_path / ".claude" / "commands" / "review.md").exists()
    assert not (tmp_path / "tkd.lock.json").exists()


@pytest.mark.asyncio
async def test_json_config_and_env_resolution(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    write(
        tmp_path / "registry" / "skills" / "backend-core" / "SKILL.md",
        (
            "---\n"
            "name: backend-core\n"
            "description: Backend core skill\n"
            "---\n\n"
            "Build backend features.\n"
        ),
    )
    write(
        tmp_path / "registry" / "skills" / "extra-skill" / "SKILL.md",
        "---\nname: extra-skill\ndescription: Extra skill\n---\n\nMore backend features.\n",
    )
    write(tmp_path / "registry" / "rules" / "python-style.mdc", "Use Python typing.\n")
    write(tmp_path / "registry" / "rules" / "tdd-workflow.mdc", "Write tests first.\n")
    write(
        tmp_path / "registry" / "commands" / "plan-endpoint.md",
        "---\ndescription: Plan endpoint\n---\n\nPlan the endpoint before coding.\n",
    )
    write(
        tmp_path / "registry" / "commands" / "review-openapi.md",
        "---\ndescription: Review OpenAPI\n---\n\nReview generated OpenAPI output.\n",
    )
    write(tmp_path / "registry" / "templates" / "ci.yml", "name: CI\n")
    write(tmp_path / "registry" / "configs" / "lint-rules.json", '{"strict": true}\n')
    write(tmp_path / "registry" / "meta" / "project-context.txt", "backend project\n")
    write(tmp_path / ".env", "UPSTASH_TOKEN=dotenv-token\n")
    write(
        tmp_path / "tkd.json",
        json.dumps(
            {
                "targets": {
                    "agents": "*",
                    "root": ".",
                },
                "sources": {
                    "local": "./registry",
                },
                "skills": {
                    "local/skills": {"include": "all"},
                },
                "rules": {
                    "local/rules": {"include": ["*"]},
                },
                "mcp": {
                    "search-api": {
                        "command": "npx",
                        "args": ["-y", "@upstash/context7"],
                        "env": {
                            "UPSTASH_REDIS_REST_URL": "${UPSTASH_URL}",
                            "UPSTASH_REDIS_REST_TOKEN": "${UPSTASH_TOKEN}",
                        },
                    }
                },
                "commands": {
                    "local/commands": {"include": "all"},
                },
                "custom": {
                    "local/templates": {
                        "include": ["*"],
                        "scope": "root",
                        "dest": ".github/workflow-templates/",
                    },
                    "local/configs": {
                        "include": ["lint-rules.json"],
                        "scope": "agents",
                        "dest": "configs/",
                    },
                    "local/meta": {
                        "include": ["project-context.txt"],
                        "scope": "root",
                        "dest": ".cursorignore",
                    },
                },
            },
            indent=2,
        ),
    )

    assert await cmd_check(Args(str(tmp_path / "tkd.json"))) == 0
    assert (
        await cmd_sync(
            Args(
                str(tmp_path / "tkd.json"),
                env=["UPSTASH_URL=https://example.upstash.io", "UPSTASH_TOKEN=cli-token"],
            )
        )
        == 0
    )

    assert (tmp_path / ".agents" / "workflows" / "plan-endpoint.md").exists()
    assert (tmp_path / ".agents" / "skills" / "backend-core" / "SKILL.md").exists()
    assert (tmp_path / ".cursor" / "commands" / "plan-endpoint.md").exists()
    assert (tmp_path / ".claude" / "commands" / "plan-endpoint.md").exists()
    assert (tmp_path / "home" / ".codex" / "prompts" / "plan-endpoint.md").exists()
    assert (tmp_path / ".agents" / "skills" / "backend-core" / "SKILL.md").exists()
    assert (tmp_path / ".gemini" / "commands" / "plan-endpoint.toml").exists()
    shared_workflow = tmp_path / ".agents" / "workflows" / "plan-endpoint.md"
    assert shared_workflow.exists()
    assert (tmp_path / ".agents" / "skills" / "backend-core" / "SKILL.md").exists()

    trae_command = tmp_path / ".trae" / "commands" / "plan-endpoint.md"
    assert trae_command.exists()

    continue_config = (tmp_path / ".continue" / "config.yaml").read_text(encoding="utf-8")
    assert "prompts:" in continue_config
    assert "name: plan-endpoint" in continue_config
    assert "rules:" in continue_config
    assert "mcpServers:" in continue_config
    assert (tmp_path / ".gemini" / "settings.json").exists()
    assert (tmp_path / "opencode.json").exists()
    assert (tmp_path / ".vscode" / "mcp.json").exists()
    assert (tmp_path / ".kiro" / "settings" / "mcp.json").exists()
    assert (tmp_path / ".trae" / "mcp.json").exists()
    assert (tmp_path / ".roo" / "mcp.json").exists()
    assert (tmp_path / "home" / ".gemini" / "antigravity" / "mcp_config.json").exists()
    assert (tmp_path / "home" / ".codeium" / "windsurf" / "mcp_config.json").exists()
    assert (tmp_path / ".opencode" / "commands" / "plan-endpoint.md").exists()
    assert (tmp_path / ".trae" / "commands" / "plan-endpoint.md").exists()
    assert (tmp_path / ".windsurf" / "workflows" / "plan-endpoint.md").exists()
    assert (tmp_path / ".github" / "prompts" / "plan-endpoint.prompt.md").exists()
    assert (tmp_path / ".kiro" / "workflows" / "plan-endpoint.md").exists()
    assert (tmp_path / ".roo" / "commands" / "plan-endpoint.md").exists()
    assert (tmp_path / ".github" / "workflow-templates" / "ci.yml").exists()
    cursorignore = (tmp_path / ".cursorignore").read_text(encoding="utf-8")
    assert cursorignore == "backend project\n"
    assert (tmp_path / ".cursor" / "configs" / "lint-rules.json").exists()
    assert (tmp_path / ".claude" / "configs" / "lint-rules.json").exists()
    assert (tmp_path / ".agents" / "configs" / "lint-rules.json").exists()
    assert (tmp_path / ".claude" / "skills" / "backend-core").exists()
    assert (tmp_path / "home" / ".codex" / "prompts" / "plan-endpoint.md").exists()
    assert (tmp_path / ".agents" / "configs" / "lint-rules.json").exists()

    cursor_mcp_path = tmp_path / ".cursor" / "mcp.json"
    cursor_mcp = json.loads(cursor_mcp_path.read_text(encoding="utf-8"))
    env = cursor_mcp["mcpServers"]["search-api"]["env"]
    assert env["UPSTASH_REDIS_REST_URL"] == "https://example.upstash.io"
    assert env["UPSTASH_REDIS_REST_TOKEN"] == "cli-token"


@pytest.mark.asyncio
async def test_sync_ask_env_prompts_before_resolving(monkeypatch, tmp_path: Path, capsys) -> None:
    write(
        tmp_path / "tkd.json",
        json.dumps(
            {
                "targets": {"agents": ["cursor"], "root": "."},
                "sources": {"local": "./registry"},
                "skills": {},
                "rules": {},
                "mcp": {
                    "search-api": {
                        "command": "npx",
                        "args": ["-y", "@upstash/context7"],
                        "env": {
                            "UPSTASH_REDIS_REST_TOKEN": "${UPSTASH_TOKEN}",
                        },
                    }
                },
                "commands": {},
                "custom": {},
            },
            indent=2,
        ),
    )

    prompts = []

    def fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return "prompted-token"

    monkeypatch.setattr("tkd.cli.CONSOLE.input", fake_input)

    assert await cmd_sync(Args(str(tmp_path / "tkd.json"), ask_env=True)) == 0

    assert prompts
    assert "UPSTASH_TOKEN" in prompts[0]


@pytest.mark.asyncio
async def test_sync_fails_fast_on_missing_env(tmp_path: Path) -> None:
    write(
        tmp_path / "tkd.json",
        json.dumps(
            {
                "targets": {"agents": ["cursor"], "root": "."},
                "sources": {"local": "./registry"},
                "skills": {},
                "rules": {},
                "mcp": {
                    "search-api": {
                        "command": "npx",
                        "args": ["-y", "@upstash/context7"],
                        "env": {
                            "UPSTASH_REDIS_REST_TOKEN": "${UPSTASH_TOKEN}",
                        },
                    }
                },
                "commands": {},
                "custom": {},
            },
            indent=2,
        ),
    )

    with pytest.raises(ValueError, match="Missing required environment variables: UPSTASH_TOKEN"):
        await cmd_sync(Args(str(tmp_path / "tkd.json")))
