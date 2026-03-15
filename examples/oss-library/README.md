# Open-Source Library Maintainer

A library author publishing to npm and PyPI, with strict CI governance, automated changelog generation, and documentation site tooling.

## Configuration (`tkd.json`)

```json
{
  "targets": {
    "agents": ["claude-code", "codex", "gemini", "copilot"],
    "root": "."
  },
  "sources": {
    "awesome_codes": "https://github.com/sickn33/antigravity-awesome-skills"
  },
  "skills": {
    "awesome_codes/skills/api-design-principles": { "include": "all" },
    "awesome_codes/skills/ab-test-setup": { "include": "all" }
  },
  "rules": {
    "awesome_codes/rules/semver": { "include": "all" },
    "awesome_codes/rules/public-api": { "include": "all" }
  },
  "commands": {
    "release": "awesome_codes/commands/release.md",
    "changelog": "awesome_codes/commands/changelog.md",
    "awesome_codes/workflows/release": { "include": "all" }
  },
  "mcp": {
    "npm-registry": {
      "command": "npx",
      "args": ["-y", "npm-mcp-server"],
      "env": {
        "NPM_TOKEN": "${NPM_TOKEN}"
      }
    },
    "github-issues": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  },
  "custom": {
    "awesome_codes/ci": {
      "include": ["*"],
      "scope": "root",
      "dest": ".github/workflows/"
    },
    "awesome_codes/templates": {
      "include": ["CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md"],
      "scope": "root",
      "dest": "./"
    }
  }
}
```

## Features

- **Versioning Discipline** — `semver-commit-messages` enforces conventional commits (`feat:`, `fix:`, `BREAKING CHANGE:`). `public-api-stability` flags any export removal as a breaking change requiring a major version bump. `deprecation-warnings` requires `@deprecated` annotations with migration instructions for at least one release cycle.
- **Release Automation** — The `/release` command orchestrates version bumping, changelog generation, and publishing. `/breaking-change-audit` scans the diff since the last tag and reports any public API surface changes.
- **Community Files** — The `custom` block ensures every clone includes `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md` at the root, plus CI workflows synced from a single source of truth.

## Registry Context (MCP)

- **npm Registry** — Agent can check published versions, compare package sizes, and verify that `peerDependencies` ranges are compatible before release.
- **GitHub Issues** — Triage bug reports, auto-label issues by affected module, and cross-reference PRs with issue numbers.

## Usage

```bash
tkd sync --env NPM_TOKEN=... --env GITHUB_TOKEN=...
```
