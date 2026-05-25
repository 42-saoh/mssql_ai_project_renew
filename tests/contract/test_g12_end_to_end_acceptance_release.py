from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "spec/development/end_to_end_acceptance_release.yaml"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _yaml(path: str | Path) -> dict:
    target = Path(path)
    if not target.is_absolute():
        target = ROOT / target
    return yaml.safe_load(target.read_text(encoding="utf-8"))


def test_g12_contract_references_existing_release_deliverables():
    spec = _yaml(SPEC_PATH)

    assert spec["scope"] == "g12-end-to-end-acceptance-release"
    for path in spec["releaseReports"].values():
        assert (ROOT / path).exists(), path
    for scenario in spec["finalAcceptanceScenarios"]:
        assert (ROOT / scenario["evidenceTest"]).exists(), scenario
    for path in spec["acceptanceEvidence"]["focusedTests"]:
        assert (ROOT / path).exists(), path


def test_g12_contract_preserves_all_prior_policy_boundaries():
    boundaries = _yaml(SPEC_PATH)["policyBoundaries"]

    assert boundaries["streamlitCallsFastApiOnly"] is True
    assert boundaries["serviceRunnerReturnsProposalsOnly"] is True
    assert boundaries["validationGateControlsArtifactPersistence"] is True
    for key in [
        "rowDataAllowed",
        "storedProcedureExecutionAllowed",
        "freeSqlExecutionAllowed",
        "ddlDmlApplyAllowed",
        "sourceApplyAllowed",
        "deployAllowed",
        "rawPromptPersistenceAllowed",
        "rawProviderResponsePersistenceAllowed",
        "rawStoredProcedureDefinitionPersistenceAllowed",
        "secretPersistenceAllowed",
        "rootDevelopmentSkillsAllowedAtRuntime",
    ]:
        assert boundaries[key] is False


def test_g12_release_reports_are_published_and_not_placeholders():
    spec = _yaml(SPEC_PATH)
    combined = "\n".join(_read(path) for path in spec["releaseReports"].values()).lower()

    assert "to be completed in g12" not in combined
    assert "status: scaffold" not in combined
    for required in [
        "acceptance",
        "security",
        "eval",
        "runbook",
        "known limitations",
        "make test",
        "streamlit calls fastapi only",
        "service codex runner returns proposals only",
        "validation gate controls artifact persistence",
        "no row data",
        "no stored procedure execution",
        "no ddl/dml apply",
        "no source apply",
        "no deploy",
        "raw prompt",
        "raw provider response",
        "secret",
    ]:
        assert required in combined


def test_g12_eval_suite_is_active_and_maps_to_acceptance_scenarios():
    spec = _yaml(SPEC_PATH)
    eval_spec = _yaml("spec/eval/v2_end_to_end_happy_paths.yaml")

    scenario_ids = {scenario["id"] for scenario in spec["finalAcceptanceScenarios"]}
    case_ids = {case["id"] for case in eval_spec["cases"]}

    assert eval_spec["status"] == "scaffold"
    assert eval_spec["releaseStatus"] == "g12-local-accepted"
    assert scenario_ids <= case_ids
    for case in eval_spec["cases"]:
        assert (ROOT / case["evidence"]).exists(), case
