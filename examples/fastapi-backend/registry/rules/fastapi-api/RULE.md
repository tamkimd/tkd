For backend API work:

- Preserve a clear separation between routers, schemas, services, and persistence code.
- Add response models and typed request bodies for every public endpoint.
- Prefer dependency-injected services instead of creating clients inside route handlers.
- Add regression tests for validation errors, auth failures, and the main success path.
- Use Context7 before changing framework integration code or configuration.
