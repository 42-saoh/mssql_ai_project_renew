# V2 Runbook

## Security Validation

Use this G11 runbook before G12 release acceptance and after any change to
policy gates, storage, observability, Metadata Gateway, Service Codex Runner,
or Streamlit API boundaries.

```bash
python -m pytest tests/contract/test_g11_security_eval_observability_hardening.py tests/security/test_g11_observability_storage_hardening.py tests/eval/test_g11_security_eval_observability_hardening_eval.py -q
make test
```

## Redaction Finding Response

1. Stop the request path at the first policy or validation gate.
2. Verify repositories contain no raw prompt, raw provider response, raw stored
   procedure definition, row data, connection string, source content, or
   secret.
3. Verify observability events contain only allowed metadata fields and safe
   blocker codes.
4. Verify blocked requests did not create approval resume side effects, runner
   submissions, persisted artifacts, DB execution, source apply, or deploy.

## Observability

LangSmith tracing remains development-only and disabled by default. Local
observability events are allowed only as sanitized platform metadata. Do not
record raw prompts, provider responses, runner stdout/stderr, SQL definitions,
row data, credentials, source files, or generated source content.

## Realm Boundary Check

Service Codex Runner runtime workspaces must be copied only from
`services/codex-runner/runtime-template`. Runtime files must not import root
`.agents/skills`, root `.codex`, root development docs, legacy reference code,
or credentials.
