# tkd — The Universal AI Agent Workspace Manager 🤖

`tkd` is an asynchronous CLI tool that distributes skills, rules, custom instructions, commands (workflows), Model Context Protocol (MCP) configs, and custom files into multiple AI-agent IDE workspaces from a single `tkd.json` configuration file.

**Write once, sync everywhere.** Whether you use Antigravity, Codex, Cursor, Claude Code, Windsurf, or GitHub Copilot, `tkd` acts as your "AI dotfiles" manager—ensuring every LLM coding assistant gets its native file layout configured automatically.

## 🚀 Why tkd?

- **Single Source of Truth**: Manage your AI context in one `tkd.json` file. Stop copying and pasting `.cursorrules` or `CLAUDE.md` across projects.
- **Cross-IDE Compatibility**: Supports 12+ major AI coding assistants (Antigravity, Codex, Cursor, Claude Code, Copilot, etc.).
- **Native MCP Support**: Define Model Context Protocol (MCP) servers inline and let `tkd` translate them into the specific JSON/TOML/YAML formats required by each agent.
- **Remote Artifact Resolution**: Pull reusable prompts, skills, and rules directly from public or private Git repositories.
- **Secret Management**: Seamlessly resolve environment variables (`${API_KEY}`) for secure MCP configurations.

## 📖 Table of Contents

- [Install](#-install)
- [Quick Start](#-quick-start)
- [CLI Commands](#-cli-commands)
- [Config Reference (`tkd.json`)](#-config-reference-tkdjson)
  - [Schema Overview](#schema-overview)
  - [`targets`](#targets)
  - [`sources`](#sources)
  - [`skills`](#skills)
  - [`rules`](#rules)
  - [`commands`](#commands)
  - [`mcp`](#mcp)
  - [`custom`](#custom)
- [Secret Resolution](#-secret-resolution)
- [Supported Agents](#-supported-agents)
- [Shared `.agents/` Layer](#-shared-agents-layer)
- [Example Configs](#-example-configs)
- [Development](#-development)

---

## ⚙️ Prerequisites

`tkd` requires **Python 3.8+**. We recommend using **uv** for the fastest installation experience, though `pip` works perfectly too.

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "ir.exe https://astral.sh/uv/install.ps1 | iex"
```

### Install Python (via uv)

```bash
uv python install 3.12
```

---

## 📦 Install

Run `tkd` directly or install it globally as a tool:

### Use without installing (`uvx`)

```bash
uvx --from git+https://github.com/tamkimd/tkd tkd sync
```

### Install as a global CLI tool (`uv`)

```bash
uv tool install git+https://github.com/tamkimd/tkd
```

### Traditional Install (`pip`)

```bash
pip install git+https://github.com/tamkimd/tkd
```

---

## ⚡ Quick Start

Get your AI workspace synced in three simple steps:

```bash
# 1. Create a starter config
tkd init

# 2. Validate what will be installed (Dry Run)
tkd check

# 3. Sync configs into your agent workspaces
tkd sync
```

---

## 🛠️ CLI Commands

### Global Options

These flags must be placed **before** the subcommand:

| Flag | Description |
|---|---|
| `--config PATH` | Path to config file (default: `tkd.json`) |
| `--env KEY=VALUE` | Pass environment variables manually (repeatable) |
| `--refresh` | Re-fetch cached Git sources instead of reusing `.tkd-cache/` |

### `tkd init`

Creates a starter `tkd.json` in the current directory.

```bash
tkd init            # fails if tkd.json already exists
tkd init --force    # overwrites existing tkd.json
```

### `tkd check`

Resolves the config, validates all artifacts, and displays a planned installation summary without writing any files (Dry run).

```bash
tkd check
tkd --config path/to/tkd.json check
tkd --env GITHUB_TOKEN=... check
tkd --refresh check
```

### `tkd sync`

Resolves all sources and writes agent-native configuration files directly into the target workspace(s).

```bash
tkd sync
tkd sync --ask-env
tkd --env UPSTASH_URL=... --env UPSTASH_TOKEN=... sync
tkd --refresh sync
```

| Flag | Description |
|---|---|
| `--ask-env` | Prompt interactively for missing environment variables instead of failing |

### `tkd help`

Show global help or help for a specific subcommand.

```bash
tkd help
tkd help sync
```

---

## 📄 Config Reference (`tkd.json`)

### Schema Overview

`tkd.json` is a flat JSON object that dictates how your AI environment is built:

| Key | Required | Type | Description |
|---|---|---|---|
| `targets` | **yes** | object | Agent layouts and workspace root. |
| `sources` | **yes** | object | Where artifacts come from (local paths or Git repos). |
| `skills` | no | object | Select skill folders to install. Default: `{}` |
| `rules` | no | object | Select rule files to install (e.g., `.cursorrules`). Default: `{}` |
| `commands` | no | object | Select command/prompt/workflow files to install. Default: `{}` |
| `mcp` | no | object | Inline Model Context Protocol (MCP) server configurations. Default: `{}` |
| `custom` | no | object | Arbitrary file mirroring. Default: `{}` |

**Minimal valid config:**

```json
{
  "targets": { "agents": "*", "root": "." },
  "sources": { "anthropic": "https://github.com/anthropics/skills" },
  "skills": { "anthropic/skills": { "include": "all" } }
}
```

---

### `targets`

Controls **which agents** to sync to, where the workspace root is, and how files are linked.

| Field | Type | Default | Description |
|---|---|---|---|
| `agents` | `string` \| `string[]` | `[]` | Agent names or `"*"` for all. |
| `root` | `string` | `"."` | Workspace root, relative to `tkd.json` location. |

**Example (All agents wildcard):**
```json
"targets": { "agents": "*", "root": "." }
```

**Example (Specific agents):**
```json
"targets": { "agents": ["cursor", "claude-code", "windsurf"], "root": "." }
```

---

### `sources`

Define repositories or local folders to pull AI context from. Keys are source names used later in the config.

| Field | Type | Required | Description |
|---|---|---|---|
| `path` | `string` | for local | Relative path to a local directory. |
| `url` | `string` | for git | Git clone URL. Supports `${VAR}` placeholders. |
| `ref` | `string` | no | Branch, tag, or commit. |
| `auth` | `object` | no | Authentication config. |

**Local source (string shorthand):**
```json
"local": "./registry"
```

**Git repo with inline token and branch:**
```json
"internal": "https://${GITHUB_TOKEN}@github.com/org/tools.git#main"
```

---

### `skills`, `rules`, & `commands`

Select which files to install. Keys use the format `{source_name}/{path}`.

| Field | Type | Default | Description |
|---|---|---|---|
| `include` | `string` \| `string[]` | `all` | Items to include. |
| `exclude` | `string[]` | `[]` | Items to exclude. |
| `enabled` | `bool` | `true` | Set `false` to skip. |

**Example (Rules / Instructions):**
```json
"rules": {
  "awesome_cursorrules/rules/python": { "include": "all" },
  "awesome_cursorrules/rules/typescript": { "exclude": ["legacy-rule"] }
}
```

---

### `mcp` (Model Context Protocol)

Define MCP server configurations inline. `tkd` translates these into the correct native format for your specific IDE. Values support `${VAR}` placeholders.

**Command-based server (npx):**
```json
"mcp": {
  "context7": {
    "command": "npx",
    "args": ["-y", "@upstash/context7"],
    "env": {
      "UPSTASH_REDIS_REST_URL": "${UPSTASH_URL}",
      "UPSTASH_REDIS_REST_TOKEN": "${UPSTASH_TOKEN}"
    }
  }
}
```

---

### `custom`

Mirror arbitrary files into the workspace root or agent config directory.

```json
"custom": {
  "ops/configs": {
    "include": ["lint-rules.json"],
    "scope": "agents",      // "root" or "agents"
    "dest": "configs/"
  }
}
```

---

## 🔐 Secret Resolution

`${VAR}` placeholders in sources and MCP configs are resolved in this priority order:

1. `--env KEY=VALUE` CLI flag
2. Shell environment variables
3. `.env` file (next to `tkd.json`)
4. Interactive prompt (only when run with `--ask-env`)

If a required variable is missing and `--ask-env` is not passed, `tkd sync` will fail fast with a clear error message.

---

## 🤖 Supported Agents

`tkd` currently supports **12 major AI agents**. Use `"agents": "*"` in your config to target all of them simultaneously.

| Agent | Config Key | Skills | Rules | Commands | MCP Config Path |
|---|---|---|---|---|---|
| **🤖 Antigravity** | `antigravity` | `.agents/skills/` | `.agents/rules/*.md` | `.agents/workflows/*.md` | `~/.gemini/antigravity/mcp_config.json` |
| **📜 Codex** | `codex` | `.agents/skills/` | `AGENTS.md` | `~/.codex/prompts/*.md` | `.codex/config.toml` |
| **🚀 Claude Code** | `claude-code` | `.claude/skills/` | `CLAUDE.md` | `.claude/commands/*.md` | `.mcp.json` |
| **✨ Cursor** | `cursor` | `.cursor/skills/` | `.cursor/rules/*.mdc` | `.cursor/commands/*.md` | `.cursor/mcp.json` |
| **🐙 GitHub Copilot** | `copilot` | `.github/skills/` | `.github/copilot-instructions.md` | `.github/prompts/*.md` | `.vscode/mcp.json` |
| **🌊 Windsurf** | `windsurf` | `.windsurf/skills/` | `.windsurf/rules/*.md` | `.windsurf/workflows/*.md` | `~/.codeium/windsurf/mcp_config.json` |
| **Roo** | `roo` | `.roo/skills/` | `.roo/rules-general/*.md` | `.roo/commands/*.md` | `.roo/mcp.json` |
| **Continue** | `continue` | `.continue/skills/` | `.continue/config.yaml` | `.continue/config.yaml` | `.continue/config.yaml` |
| **Gemini** | `gemini` | `.gemini/skills/` | `GEMINI.md` | `.gemini/commands/*.toml` | `.gemini/settings.json` |
| **OpenCode** | `opencode` | `.opencode/skills/` | `AGENTS.md` | `.opencode/commands/*.md` | `opencode.json` |
| **Trae** | `trae` | `.trae/skills/` | `.trae/rules/*.md` | `.trae/commands/*.md` | `.trae/mcp.json` |
| **Kiro** | `kiro` | `.kiro/skills/` | `.kiro/steering/*.md` | `.kiro/workflows/*.md` | `.kiro/settings/mcp.json` |

> **Note:** Codex prompts are written to the global `~/.codex/prompts/` directory. Antigravity and Windsurf MCP configs are also written to global paths.

---

## 📂 Shared `.agents/` Layer

Every `tkd sync` materializes a portable `.agents/` directory inside your workspace root:

```text
.agents/
  skills/
    backend-core/
      SKILL.md
  rules/
    python-style.md
  workflows/
    plan-endpoint.md
```

This layer is always created, regardless of which specific agents you select. It serves as an agent-agnostic universal format—a perfect deployment target and single source of truth for your team's context.

---

## 💡 Example Configs

Check out the `examples/` directory for ready-to-use configurations:

| Example | Purpose |
|---|---|
| **Polyglot Enterprise** | Multi-language, operational workflows, live infra MCP. |
| **AI/ML Research Lab** | Jupyter, PyTorch rules, experiment tracking (W&B, HF). |
| **Solo Indie SaaS** | Capacitor/FastAPI, Stripe, transactional email, mobile rules. |
| **OSS Library** | Strict CI, SemVer rules, release automation, triage. |
| **fastapi-backend** | A complete local/git hybrid example you can run now. |

---

## 👨‍💻 Development

### Installation (Local Development)

```bash
uv sync --extra dev
```

### Tests

```bash
uv run pytest -q
```

Coverage is enforced at 70% minimum. Tests use `pytest-asyncio` and `pytest-cov`.

### Linting & Formatting

```bash
uvx ruff check .
uvx ruff check . --fix
```
