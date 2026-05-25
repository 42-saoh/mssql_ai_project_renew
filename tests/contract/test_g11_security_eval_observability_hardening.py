from pathlib import Path

import yaml

from apps.api.api_app.services.observability_service import build_observability_event

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "spec/development/security_eval_observability_hardening.yaml"


def _spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def test_g11_contract_references_existing_deliverables():
    spec = _spec()

    assert SPEC_PATH.exists()
    assert (ROOT / spec["storageRedaction"]["service"]).exists()
    assert (ROOT / spec["storageRedaction"]["redactionValidator"]).exists()
    assert (ROOT / spec["observability"]["langsmithContract"]).exists()
    assert (ROOT / spec["observability"]["safeEventService"]).exists()
    assert (ROOT / spec["observability"]["safeEventRepository"]).exists()
    for path in [
        spec["releaseRunbooks"]["securityReport"],
        spec["releaseRunbooks"]["evalReport"],
        spec["releaseRunbooks"]["runbook"],
    ]:
        assert (ROOT / path).exists(), path
    for path in spec["acceptanceEvidence"]["focusedTests"]:
        assert (ROOT / path).exists(), path


def test_g11_contract_preserves_security_boundaries():
    spec = _spec()
    boundaries = spec["policyBoundaries"]

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


def test_g11_safe_observability_event_shape_matches_contract():
    spec = _spec()
    event = build_observability_event(
        "chat_run_recorded",
        subject_type="chat_run",
        subject_id="chatrun_contract",
        chat_run_id="chatrun_contract",
        conversation_id="conv_contract",
        intent="SP_ANALYSIS",
        route="codex_runner",
        status="ACCEPTED",
        policy_decision="ALLOW",
        blocker_codes=[],
    )

    assert set(event) <= set(spec["observability"]["allowedEventFields"])
    assert event["event_type"] == "chat_run_recorded"
    assert event["subject_type"] == "chat_run"
    assert event["blocker_codes"] == []


def test_g11_release_docs_are_not_placeholders_and_cover_response_steps():
    spec = _spec()
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in [
            spec["releaseRunbooks"]["securityReport"],
            spec["releaseRunbooks"]["evalReport"],
            spec["releaseRunbooks"]["runbook"],
        ]
    ).lower()

    assert "to be completed in g12" not in combined
    for required in [
        "storage redaction",
        "observability",
        "validation",
        "incident response",
        "raw prompt",
        "raw provider response",
        "stored procedure",
        "row data",
        "secret",
    ]:
        assert required in combined
