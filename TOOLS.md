# Tools

## Development commands

```bash
make test
make test-contract
make test-unit
make test-integration
make test-security
make test-eval
make test-e2e
make lint
make typecheck
```

## Service runtime commands

Service Codex Runner uses `codex exec` in isolated workspaces. Development Codex must not call runtime `codex exec` as if it were a development goal.
