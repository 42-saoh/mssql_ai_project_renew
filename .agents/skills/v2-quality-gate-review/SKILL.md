---
name: v2-quality-gate-review
description: Review cross-realm boundaries, safety policy, tests, evals, and release readiness.
---

# v2-quality-gate-review

Use this skill only in the Development Codex Realm.

## Steps

1. Read root `AGENTS.md`, `POLICY.md`, `ARCHITECTURE.md`, and the active `goals/Gxx-*.md` file.
2. Identify required deliverables and non-goals.
3. Make the smallest contract-first change that satisfies the goal.
4. Add or update tests.
5. Run the validation commands from the goal.
6. Report changed files, validation results, and remaining risks.

## Forbidden

- Do not copy legacy implementation code.
- Do not weaken blocked-operation policy.
- Do not merge Development Codex and Service Codex Runner realms.
