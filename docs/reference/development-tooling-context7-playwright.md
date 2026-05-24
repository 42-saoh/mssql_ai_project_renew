# Development Tooling: Context7 and Playwright

Context7 and Playwright are Development Codex tools for implementation support and local UI verification. They do not change production behavior, service runtime behavior, storage policy, or safety policy.

## Context7

Use `.agents/skills/context7-docs` when a task depends on current framework, library, API, configuration, migration, or CLI documentation. Identify the library and likely version from the repo before querying.

Configuration:

```dotenv
PLF_CONTEXT7_ENABLED=false
CONTEXT7_API_KEY=
```

Rules:

- Use Context7 for external vendor documentation, not for repo-internal facts.
- Do not send secrets, credentials, connection strings, raw prompts, provider responses, row data, stored procedure definitions, or large proprietary code blobs.
- Prefer official or vendor documentation.
- If external docs conflict with project policy, project policy wins.

## Playwright

Use `.agents/skills/browser-automation-smoke` for non-destructive local UI smoke tests, screenshots, and happy-path checks against localhost or approved dev/test URLs.

Configuration:

```dotenv
PLF_PLAYWRIGHT_SMOKE_ENABLED=false
PLAYWRIGHT_BASE_URL=http://127.0.0.1:8501
PLAYWRIGHT_BROWSER=chromium
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_BROWSERS_PATH=
```

Install browser binaries only when smoke tests are needed:

```bash
python -m playwright install chromium
```

Rules:

- Playwright smoke is disabled by default and runs only when `PLF_PLAYWRIGHT_SMOKE_ENABLED=true`.
- Do not use production or shared real accounts.
- Do not submit real payments, approvals, emails, or irreversible actions.
- Treat cookies, tokens, screenshots, traces, and storage state as sensitive.
- Do not commit screenshots, videos, traces, browser storage state, or captured secrets.

## Reporting

When either tool is used, report the tool, target library or URL, version assumption, routes visited or docs consulted, observed assertions, and blockers. Keep evidence sanitized.
