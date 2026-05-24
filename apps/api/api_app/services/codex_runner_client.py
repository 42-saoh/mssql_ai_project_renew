from __future__ import annotations


def submit_codex_run(request: dict) -> dict:
    return {"status": "SUBMITTED", "request": request}
