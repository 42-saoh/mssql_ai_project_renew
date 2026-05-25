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

## G12 Release Acceptance

Run the focused G12 acceptance command first:

```bash
python -m pytest tests/contract/test_g12_end_to_end_acceptance_release.py tests/e2e/test_g12_end_to_end_acceptance_release_e2e.py tests/eval/test_g12_end_to_end_acceptance_release_eval.py -q
```

Then run the full release gate:

```bash
make test
```

The complete release gate also maps to the required `EVAL_SPEC.md` targets:
`make test-contract`, `make test-unit`, `make test-integration`,
`make test-security`, `make test-eval`, and `make test-e2e`.

Release acceptance requires the published acceptance, security, eval, runbook,
and known limitations reports to remain non-placeholder documents. Do not mark
G12 accepted if any report removes or weakens Streamlit calls FastAPI only,
Service Codex Runner returns proposals only, validation gate controls artifact
persistence, no row data, no stored procedure execution, no DDL/DML apply, no
source apply, no deploy, raw prompt, raw provider response, or secret storage
boundaries.
