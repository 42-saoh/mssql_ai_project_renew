from __future__ import annotations

from .fake_runner import run_fake
from .real_runner import DEFAULT_RUNTIME_TEMPLATE, DEFAULT_WORKSPACE_BASE, RealRunnerConfig, submit_real_run
from .validator import validate_result


def submit_run(
    request: dict,
    evidence_bundle: dict | None = None,
    mode: str = "fake",
    *,
    workspace_base: str | None = None,
    runtime_template: str | None = None,
    run_command=None,
) -> dict:
    if mode == "real":
        config = RealRunnerConfig(
            workspace_base=workspace_base or DEFAULT_WORKSPACE_BASE,
            runtime_template=runtime_template or DEFAULT_RUNTIME_TEMPLATE,
        )
        return submit_real_run(request, evidence_bundle, config=config, run_command=run_command)
    if mode != "fake":
        raise ValueError(f"Unknown runner mode: {mode}")
    result = run_fake(request, evidence_bundle)
    valid, blockers = validate_result(result)
    result["validation"]["policyValid"] = valid
    result["blockers"] = blockers
    return result
