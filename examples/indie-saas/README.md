# Solo Indie SaaS (Capacitor + FastAPI)

A solo developer building a mobile-first SaaS with an Ionic/Capacitor frontend and a FastAPI backend, integrating payment processing and transactional email.

## Configuration (`tkd.json`)

```json
{
  "targets": {
    "agents": ["cursor", "claude-code", "copilot"],
    "root": "."
  },
  "sources": {
    "awesome_skills": "https://github.com/sickn33/antigravity-awesome-skills",
    "anthropic": "https://github.com/anthropics/skills"
  },
  "skills": {
    "awesome_skills/skills/fastapi-pro": { "include": "all" },
    "awesome_skills/skills/stripe-integration": { "include": "all" },
    "anthropic/skills/claude-api": { "include": "all" }
  },
  "rules": {
    "awesome_skills/rules/api": { "include": "all" },
    "awesome_skills/rules/mobile": { "include": "all" }
  },
  "commands": {
    "awesome_skills/workflows/common": { "include": "all" }
  },
  "mcp": {
    "stripe-mcp": {
      "command": "npx",
      "args": ["-y", "@stripe/mcp", "--tools=all"],
      "env": {
        "STRIPE_SECRET_KEY": "${STRIPE_SK}"
      }
    },
    "resend-email": {
      "command": "npx",
      "args": ["-y", "resend-mcp"],
      "env": {
        "RESEND_API_KEY": "${RESEND_KEY}"
      }
    },
    "supabase": {
      "command": "npx",
      "args": ["-y", "supabase-mcp-server"],
      "env": {
        "SUPABASE_URL": "${SUPABASE_URL}",
        "SUPABASE_SERVICE_KEY": "${SUPABASE_KEY}"
      }
    },
    "sentry-issues": {
      "command": "npx",
      "args": ["-y", "@sentry/mcp-server"],
      "env": {
        "SENTRY_AUTH_TOKEN": "${SENTRY_TOKEN}"
      }
    }
  },
  "custom": {
    "awesome_skills/capacitor": {
      "include": ["capacitor.config.ts"],
      "scope": "root",
      "dest": "./"
    },
    "awesome_skills/github": {
      "include": ["*"],
      "scope": "root",
      "dest": ".github/workflows/"
    }
  }
}
```

## Features

- **Full-Stack Skills** — FastAPI backend skill enforces router/schema/service separation. Ionic Capacitor skill handles native plugin bridge patterns. Stripe skill covers webhook signature verification and idempotency keys.
- **Mobile-First Rules** — `capacitor-plugin-guards` ensures all native plugin calls are wrapped in platform-availability checks. `mobile-first-css` enforces min-width breakpoints and touch-target sizing.

## Payment & Comms (MCP)

- **Stripe** — Agent can create test charges, inspect webhook events, and generate checkout sessions without switching to the Stripe dashboard.
- **Resend** — Send transactional emails and inspect delivery logs from within the editor.
- **Supabase** — Query tables, manage RLS policies, and generate typed client code against the live schema.
- **Sentry** — Browse recent errors, view stack traces, and link issues to code changes.

## Usage

```bash
tkd sync --env STRIPE_SK=... --env RESEND_KEY=... --env SUPABASE_URL=... --env SUPABASE_KEY=... --env SENTRY_TOKEN=...
```
