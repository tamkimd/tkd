# Polyglot Enterprise Stack

A multi-language environment with Python, Java, Node.js, Next.js, and DevOps tooling — governed by curated community rules, operational workflows, and live infrastructure MCP servers.

## Configuration (`tkd.json`)

```json
{
  "targets": {
    "agents": "*",
    "root": "."
  },
  "sources": {
    "ops_workflows": "https://github.com/wshobson/commands",
    "awesome_cursorrules": "https://github.com/PatrickJS/awesome-cursorrules"
  },
  "rules": {
    "awesome_cursorrules/rules/java-springboot-jpa-cursorrules-prompt-file": { "include": "all" },
    "awesome_cursorrules/rules/python-llm-ml-workflow-cursorrules-prompt-file": { "include": "all" },
    "awesome_cursorrules/rules/es-module-nodejs-guidelines-cursorrules-prompt-fil": { "include": "all" },
    "awesome_cursorrules/rules/typescript-nodejs-nextjs-react-ui-css-cursorrules": {
      "include": "all",
      "exclude": ["legacy-pages-router"]
    }
  },
  "commands": {
    "review": "ops_workflows/workflows/full-review.md",
    "fix": "ops_workflows/workflows/smart-fix.md",
    "tdd": "ops_workflows/workflows/tdd-cycle.md",
    "deploy-check": "ops_workflows/tools/deploy-checklist.md",
    "db-migrate": "ops_workflows/tools/db-migrate.md"
  },
  "mcp": {
    "postgres-context": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost:5432/main"]
    },
    "k8s-manager": {
      "command": "npx",
      "args": ["-y", "mcp-server-kubernetes"]
    },
    "next-diagnostics": {
      "command": "npx",
      "args": ["-y", "next-devtools-mcp@latest"]
    },
    "terraform-registry": {
      "command": "npx",
      "args": ["-y", "terraform-mcp-server"]
    }
  },
  "custom": {
    "ops_workflows/configs": {
      "include": [".editorconfig", "docker-compose.yml"],
      "scope": "root",
      "dest": "./"
    }
  }
}
```

## Features

- **Operational Workflows** — The `commands` block maps the `wshobson/commands` source to shorthand triggers. Running `/review` or `/fix` invokes multi-step analysis covering architecture, security, and performance.
- **Backend Integrity** — Python rules enforce the RORO pattern and `async def` for I/O. Java rules mandate constructor-only injection to prevent `NullPointerException` during bean initialization.
- **Fullstack Boundaries** — The Next.js ruleset minimizes `'use client'` directives, favoring React Server Components (RSC) to optimize bundle size and SEO. Legacy pages router rules are excluded.
- **Infrastructure Governance** — Docker rules enforce multi-stage builds to strip build-time secrets from production images. Kubernetes rules require Helm charts and GitOps principles.

## Live Context (MCP)

- **Postgres** — Agent can inspect table schemas and generate valid SQL queries against the running database.
- **Kubernetes** — Connects to local kubeconfig for natural language debugging of crash-looping pods.
- **Next DevTools** — Provides real-time access to App Router routes and hydration error logs.
- **Terraform** — Accesses the live provider registry to ensure generated HCL uses the latest attribute schemas.

## Usage

```bash
tkd sync
```
