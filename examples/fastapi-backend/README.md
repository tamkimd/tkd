# fastapi-backend (Working Example)

A complete, runnable example combining public skills, local backend-specific assets, and workspace-native layouts.

## Configuration (`tkd.json`)

```json
{
  "targets": {
    "agents": "*",
    "root": "."
  },
  "sources": {
    "awesome_skills": "https://github.com/sickn33/antigravity-awesome-skills",
    "anthropic": "https://github.com/anthropics/skills",
    "local": "./registry"
  },
  "skills": {
    "local/skills": { "include": "all" },
    "anthropic/skills/claude-api": { "include": "all" }
  },
  "rules": {
    "local/rules": { "include": "all" }
  },
  "commands": {
    "local/commands": { "include": "all" }
  },
  "mcp": {
    "upstash-redis": {
      "command": "npx",
      "args": ["-y", "@upstash/mcp-server"],
      "env": {
        "UPSTASH_REDIS_REST_URL": "${UPSTASH_URL}",
        "UPSTASH_REDIS_REST_TOKEN": "${UPSTASH_TOKEN}"
      }
    }
  },
  "custom": {
    "local/configs": {
      "include": ["lint-rules.json"],
      "scope": "agents",
      "dest": "configs/"
    }
  }
}
```

## Features

- **Public & Local Integration** — Combines public skills from GitHub (`anthropic`) with local backend-specific skills, rules, and commands.
- **Agent Expansion** — Uses `"agents": "*"` to target all supported agent layouts simultaneously.
- **Custom Assets** — Demonstrates root-scoped and agent-scoped custom file synchronization.
- **Secure Configuration** — Uses environment variable placeholders (`${UPSTASH_TOKEN}`) for sensitive MCP server credentials.

## Usage

1. **Navigate to the example folder:**
   ```bash
   cd examples/fastapi-backend
   ```

2. **Run sync:**
   ```bash
   tkd sync --env UPSTASH_URL=... --env UPSTASH_TOKEN=...
   ```
