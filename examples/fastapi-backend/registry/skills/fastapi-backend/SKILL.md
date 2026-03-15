---
name: fastapi-backend
description: Build and modify FastAPI backends with consistent routing, schemas, service boundaries, and test coverage.
---

Use this skill when the task touches a FastAPI backend.

Workflow:

1. Inspect the existing app layout before adding endpoints or services.
2. Keep HTTP concerns in routers and move business logic into service modules.
3. Use Pydantic models for request and response contracts.
4. Validate error handling, status codes, and dependency injection paths.
5. Add or update tests for the changed behavior.

Implementation rules:

- Prefer explicit response models on routes.
- Keep database access behind repository or service functions.
- Use async route handlers only when the underlying stack is async.
- Group route modules by resource, not by HTTP verb.
- Avoid leaking ORM models directly through the API.

If Context7 is available, use it for FastAPI, Pydantic, SQLAlchemy, Alembic, and testing-library documentation before introducing framework-specific changes.
