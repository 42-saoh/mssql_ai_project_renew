# Service Runtime Architecture

```text
run_request + evidence_bundle
        |
        v
isolated runtime workspace
        |
        v
runtime-only docs + runtime-only skills
        |
        v
codex exec
        |
        v
schema-valid result proposal
        |
        v
platform validation gate
```

The runner must not persist artifacts directly and must not modify repository source files.
