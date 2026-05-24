# Architecture

```text
[Streamlit Internal UI]
        |
        v
[FastAPI API Gateway / Service Layer]
        |
        v
[LangGraph Chat Orchestrator]
   |              |                 |
   |              |                 +--> PLF History / Artifact Store
   |              |
   |              +--------------------> External MSSQL MCP / Metadata Gateway
   |
   +-----------------------------------> Service Codex Runner
                                           codex exec
                                           isolated workspace
                                           runtime-template only
                                           output schema
                                           validation gate
```

## Component responsibilities

| Component | Responsibility | Forbidden |
|---|---|---|
| Streamlit | Chat, History, Artifact UI | DB/MCP/Runner direct calls |
| FastAPI | API boundary, auth/RBAC, storage, validation, runner gateway | UI bypass side effects |
| LangGraph | intent, slot, policy, route, checkpoint, approval | raw payload persistence |
| External MSSQL MCP | read-only metadata evidence through REST tool boundary | row data, SP execution, free SQL, DDL/DML |
| Service Codex Runner | artifact proposals | repo source write, DB credential, artifact persistence |
| PLF Store | sanitized history/artifact/validation | raw SP, raw prompt, provider response, row data, secret |

## Dual Codex Realm

Development Codex builds this repository. Service Codex Runner generates artifact proposals for service requests. They are separate trust realms.

The boundary is contract-first:

- Development Codex uses root docs, root `.codex`, root `.agents/skills`, and
  Codex CLI `/goal`.
- Service Codex Runner uses only files copied from
  `services/codex-runner/runtime-template` into isolated runtime workspaces.
- Docs, configs, agents, skills, workspaces, credentials, and audit boundaries
  are not shared across realms.
- The machine-readable contract is
  `spec/development/dual_codex_realm_contract.yaml`.
