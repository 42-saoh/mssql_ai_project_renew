# Runtime Eval Specification

Runtime output must pass:

- output JSON schema validation
- blocked operation validation
- redaction validation
- artifact type validation
- `productionReady == false`
- review marker visibility validation

Failure means the platform must not persist the result as an artifact.
