# LangSmith Development Tracing

LangSmith tracing is available only for local or development debugging of the PLF DB Agent V2 orchestration boundary. It must not change runtime behavior, storage policy, artifact persistence, or safety decisions.

## Enable Locally

Set all required flags:

```dotenv
PLF_ENVIRONMENT=dev
PLF_LANGSMITH_ENABLED=true
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=plf-db-agent-v2-dev
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

If any required value is missing, tracing is disabled. In non-`dev` environments tracing remains disabled even when an API key is present.

## Trace Policy

Allowed trace metadata:

- `environment`
- `intent`
- `policyDecision`
- `route`
- `pgptUsed`
- `pgptModel`
- `pgptFallbackReason`

Forbidden trace data:

- raw user prompts
- raw provider responses
- raw stored procedure definitions
- row data
- secrets, API keys, tokens, and connection strings

LangSmith is a development observability tool, not a persistence layer. Do not use it to store prompts, generated artifacts, DB evidence, or approval records.

## Implementation Notes

The orchestration package owns the LangSmith guard. It uses a no-op context manager unless all development-only activation conditions pass, then wraps the safe orchestration section with `langsmith.tracing_context(...)`.
