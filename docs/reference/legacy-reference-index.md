# Legacy Reference Index

The uploaded legacy project is frozen as reference-only material. V2 is a
greenfield implementation and must not depend on legacy code at runtime.

The canonical G00 freeze contract is
`spec/reference/legacy_reference_freeze.yaml`.

Allowed reference use:

- product intent and terminology
- artifact taxonomy decisions
- policy boundary lessons
- eval and regression themes

Forbidden use:

- copying legacy implementation modules, services, routes, adapters, UI code,
  prompts, or migrations into V2
- importing, executing, packaging, or deploying legacy project code from V2
- promoting legacy runtime prompt files into active V2 runtime files
- using the legacy project to relax V2 policy or merge Codex realms

Reference docs:

- `docs/reference/legacy-policy-lessons.md`
- `docs/reference/legacy-artifact-taxonomy.md`
- `docs/reference/legacy-eval-lessons.md`
- `docs/reference/legacy-do-not-copy.md`
