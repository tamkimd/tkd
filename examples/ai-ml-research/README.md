# AI/ML Research Lab

A data science and ML engineering workspace with Jupyter conventions, PyTorch style guides, experiment tracking, and GPU-aware inference tooling.

## Configuration (`tkd.json`)

```json
{
  "targets": {
    "agents": ["cursor", "claude-code", "gemini", "continue"],
    "root": "."
  },
  "sources": {
    "awesome_cursorrules": "https://github.com/PatrickJS/awesome-cursorrules",
    "awesome_skills": "https://github.com/sickn33/antigravity-awesome-skills",
    "ops": "https://github.com/wshobson/commands"
  },
  "skills": {
    "awesome_skills/skills/python-fastapi-pro": { "include": "all" },
    "awesome_skills/skills/ab-test-setup": { "include": "all" }
  },
  "rules": {
    "awesome_cursorrules/rules/pytorch-best-practices-cursorrules-prompt-file": { "include": "all" },
    "awesome_cursorrules/rules/numpy-vectorization-cursorrules-prompt-file": { "include": "all" },
    "awesome_cursorrules/rules/pandas-method-chaining-cursorrules-prompt-file": { "include": "all" }
  },
  "commands": {
    "ops/workflows": { "include": "all" }
  },
  "mcp": {
    "huggingface-hub": {
      "command": "uvx",
      "args": ["mcp-server-huggingface"],
      "env": {
        "HF_TOKEN": "${HUGGINGFACE_TOKEN}"
      }
    },
    "wandb-experiments": {
      "command": "uvx",
      "args": ["wandb-mcp-server"],
      "env": {
        "WANDB_API_KEY": "${WANDB_KEY}",
        "WANDB_PROJECT": "main-experiments"
      }
    },
    "jupyter-kernel": {
      "command": "uvx",
      "args": ["jupyter-mcp-server"],
      "env": {
        "JUPYTER_URL": "http://localhost:8888",
        "JUPYTER_TOKEN": "${JUPYTER_TOKEN}"
      }
    }
  },
  "custom": {
    "ops/templates": {
      "include": ["*.ipynb"],
      "scope": "root",
      "dest": "templates/notebooks/"
    },
    "ops/configs": {
      "include": ["pyproject.toml", ".pre-commit-config.yaml"],
      "scope": "root",
      "dest": "./"
    }
  }
}
```

## Features

- **ML-Specific Rules** — PyTorch best practices (proper `.to(device)` usage, `torch.no_grad()` in eval, gradient checkpointing). NumPy vectorization rules forbid Python-level loops over arrays. Pandas method chaining keeps transformations readable and debuggable.
- **Template Notebooks** — The `custom` block seeds new projects with standardized notebook templates for EDA, training, and evaluation.

## Live Context (MCP)

- **Weights & Biases** — Agent can query past experiment metrics, compare runs, and log new experiments directly from the conversation.
- **HuggingFace Hub** — Browse model cards, check dataset schemas, and pull pretrained weights without leaving the editor.
- **Jupyter** — Execute cells in running kernels to validate data pipelines and inspect tensor shapes interactively.

## Usage

```bash
tkd sync --env HUGGINGFACE_TOKEN=... --env WANDB_KEY=...
```
