from __future__ import annotations

from typing import Dict

from tkd.common.models import AgentLayout, ArtifactLayout

AGENT_LAYOUTS: dict[str, AgentLayout] = {
    "antigravity": AgentLayout(
        name="antigravity",
        config_dir=".agents",
        rules=ArtifactLayout(mode="directory", path=".agents/rules"),
        commands=ArtifactLayout(mode="directory", path=".agents/workflows"),
        mcp=ArtifactLayout(mode="global_file", path="~/.gemini/antigravity/mcp_config.json"),
    ),
    "codex": AgentLayout(
        name="codex",
        config_dir=".codex",
        rules=ArtifactLayout(mode="document", path="AGENTS.md"),
        commands=ArtifactLayout(mode="directory", path="~/.codex/prompts"),
        mcp=ArtifactLayout(mode="file", path=".codex/config.toml", suffix=".toml"),
    ),
    "claude-code": AgentLayout(
        name="claude-code",
        config_dir=".claude",
        rules=ArtifactLayout(mode="document", path="CLAUDE.md"),
        commands=ArtifactLayout(mode="directory", path=".claude/commands"),
        mcp=ArtifactLayout(mode="file", path=".mcp.json", suffix=".json"),
    ),
    "gemini": AgentLayout(
        name="gemini",
        config_dir=".gemini",
        rules=ArtifactLayout(mode="document", path="GEMINI.md"),
        commands=ArtifactLayout(mode="directory", path=".gemini/commands", suffix=".toml"),
        mcp=ArtifactLayout(mode="file", path=".gemini/settings.json", suffix=".json"),
    ),
    "continue": AgentLayout(
        name="continue",
        config_dir=".continue",
        rules=ArtifactLayout(mode="embedded", path=".continue/config.yaml", suffix=".yaml"),
        commands=ArtifactLayout(mode="embedded", path=".continue/config.yaml", suffix=".yaml"),
        mcp=ArtifactLayout(mode="embedded", path=".continue/config.yaml", suffix=".yaml"),
    ),
    "cursor": AgentLayout(
        name="cursor",
        config_dir=".cursor",
        rules=ArtifactLayout(mode="directory", path=".cursor/rules", suffix=".mdc"),
        commands=ArtifactLayout(mode="directory", path=".cursor/commands"),
        mcp=ArtifactLayout(mode="file", path=".cursor/mcp.json", suffix=".json"),
    ),
    "opencode": AgentLayout(
        name="opencode",
        config_dir=".opencode",
        rules=ArtifactLayout(mode="document", path="AGENTS.md"),
        commands=ArtifactLayout(mode="directory", path=".opencode/commands"),
        mcp=ArtifactLayout(mode="file", path="opencode.json", suffix=".json"),
    ),
    "trae": AgentLayout(
        name="trae",
        config_dir=".trae",
        rules=ArtifactLayout(mode="directory", path=".trae/rules"),
        commands=ArtifactLayout(mode="directory", path=".trae/commands"),
        mcp=ArtifactLayout(mode="file", path=".trae/mcp.json", suffix=".json"),
    ),
    "windsurf": AgentLayout(
        name="windsurf",
        config_dir=".windsurf",
        rules=ArtifactLayout(mode="directory", path=".windsurf/rules"),
        commands=ArtifactLayout(mode="directory", path=".windsurf/workflows"),
        mcp=ArtifactLayout(mode="global_file", path="~/.codeium/windsurf/mcp_config.json"),
    ),
    "copilot": AgentLayout(
        name="copilot",
        config_dir=".github",
        rules=ArtifactLayout(mode="document", path=".github/copilot-instructions.md"),
        commands=ArtifactLayout(mode="directory", path=".github/prompts", suffix=".prompt.md"),
        mcp=ArtifactLayout(mode="file", path=".vscode/mcp.json", suffix=".json"),
    ),
    "kiro": AgentLayout(
        name="kiro",
        config_dir=".kiro",
        rules=ArtifactLayout(mode="directory", path=".kiro/steering"),
        commands=ArtifactLayout(mode="directory", path=".kiro/workflows"),
        mcp=ArtifactLayout(mode="file", path=".kiro/settings/mcp.json", suffix=".json"),
    ),
    "roo": AgentLayout(
        name="roo",
        config_dir=".roo",
        rules=ArtifactLayout(mode="directory", path=".roo/rules-general"),
        commands=ArtifactLayout(mode="directory", path=".roo/commands"),
        mcp=ArtifactLayout(mode="file", path=".roo/mcp.json", suffix=".json"),
    ),
}


def get_agent_layout(name: str) -> AgentLayout:
    try:
        return AGENT_LAYOUTS[name]
    except KeyError as exc:
        raise ValueError("Unsupported agent layout: {0}".format(name)) from exc
