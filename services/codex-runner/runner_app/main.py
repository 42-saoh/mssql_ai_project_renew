from __future__ import annotations

from .fake_runner import run_fake
from .validator import validate_result


def submit_run(request: dict, evidence_bundle: dict | None = None, mode: str = "fake") -> dict:
    if mode != "fake":
        raise NotImplementedError("Real codex exec is wired in G07/G08 and should be gated in CI.")
    result = run_fake(request, evidence_bundle)
    valid, blockers = validate_result(result)
    result["validation"]["policyValid"] = valid
    result["blockers"] = blockers
    return result
