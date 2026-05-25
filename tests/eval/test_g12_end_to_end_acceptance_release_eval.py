from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def test_g12_end_to_end_eval_cases_are_declared_and_have_evidence():
    release = _yaml("spec/development/end_to_end_acceptance_release.yaml")
    eval_suite = _yaml("spec/eval/v2_end_to_end_happy_paths.yaml")

    assert eval_suite["status"] == "scaffold"
    assert eval_suite["releaseStatus"] == "g12-local-accepted"
    expected_ids = {case["id"] for case in release["finalAcceptanceScenarios"]}
    actual_ids = {case["id"] for case in eval_suite["cases"]}
    assert expected_ids <= actual_ids
    for case in eval_suite["cases"]:
        assert (ROOT / case["evidence"]).exists(), case


def test_g12_eval_spec_and_release_docs_include_final_gate_language():
    eval_spec = (ROOT / "EVAL_SPEC.md").read_text(encoding="utf-8")
    acceptance = (ROOT / "docs/release/v2-acceptance-report.md").read_text(encoding="utf-8")
    limitations = (ROOT / "docs/release/v2-known-limitations.md").read_text(encoding="utf-8")

    assert "v2_end_to_end_happy_paths" in eval_spec
    assert "G12 Final Acceptance" in acceptance
    assert "Release Decision" in acceptance
    assert "Known Limitations" in limitations
    assert "production deployment" in limitations.lower()
