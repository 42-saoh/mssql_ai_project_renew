from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "spec/development/artifact_history_approval_ux_completion.yaml"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def test_g10_contract_files_and_openapi_paths_exist():
    spec = _spec()
    openapi = yaml.safe_load(_read(spec["apiCompletion"]["openapiContract"]))

    assert spec["scope"] == "g10-artifact-history-approval-ux-completion"
    for path in spec["apiCompletion"]["routeModules"].values():
        assert (ROOT / path).exists(), path
    for path in spec["apiCompletion"]["serviceModules"].values():
        assert (ROOT / path).exists(), path

    for endpoint in spec["apiCompletion"]["endpoints"].values():
        assert endpoint in openapi["paths"], endpoint


def test_g10_validation_history_and_approval_contract_preserves_safety():
    spec = _spec()
    validation_gate = spec["validationGate"]
    history_policy = spec["historyPolicy"]
    approval_policy = spec["approvalPolicy"]
    boundaries = spec["policyBoundaries"]

    assert validation_gate["artifactPersistenceRequiresValidation"] is True
    assert validation_gate["persistedArtifactContentInlineAllowed"] is False
    assert validation_gate["persistedArtifactProductionReadyAllowed"] is False
    assert validation_gate["tableDesignPreviewPersistenceAllowed"] is False

    assert history_policy["conversationListReturnsSanitizedMetadataOnly"] is True
    assert history_policy["rawUserMessageReturned"] is False
    assert history_policy["rawPromptReturned"] is False
    assert history_policy["rawProviderResponseReturned"] is False
    assert history_policy["rowDataReturned"] is False
    assert history_policy["rawStoredProcedureDefinitionReturned"] is False
    assert history_policy["secretReturned"] is False

    assert approval_policy["approvalsAreReviewMetadataOnly"] is True
    assert approval_policy["resumeApprovalExecutesDbOrRunner"] is False
    assert approval_policy["resumeApprovalPersistsArtifacts"] is False

    assert boundaries["streamlitCallsFastApiOnly"] is True
    assert boundaries["serviceRunnerReturnsProposalsOnly"] is True
    assert boundaries["validationGateControlsArtifactPersistence"] is True
    assert boundaries["rowDataAllowed"] is False
    assert boundaries["storedProcedureExecutionAllowed"] is False
    assert boundaries["ddlDmlApplyAllowed"] is False
    assert boundaries["sourceApplyAllowed"] is False
    assert boundaries["deployAllowed"] is False
    assert boundaries["rawPromptPersistenceAllowed"] is False
    assert boundaries["rawProviderResponsePersistenceAllowed"] is False
    assert boundaries["secretPersistenceAllowed"] is False


def test_g10_streamlit_ux_uses_declared_fastapi_client_methods():
    spec = _spec()
    client_text = _read(spec["uiCompletion"]["apiClientPath"])

    for page in spec["uiCompletion"]["pages"].values():
        page_text = _read(page["path"])
        assert "ApiClient(" in page_text
        assert "requests." not in page_text
        for method in page["apiClientMethods"]:
            assert f"def {method}(" in client_text
            assert f"client.{method}(" in page_text
        for state in page["visibleStates"]:
            assert state in page_text

    combined_text = "\n".join(
        _read(path)
        for path in [
            spec["uiCompletion"]["apiClientPath"],
            *(page["path"] for page in spec["uiCompletion"]["pages"].values()),
        ]
    )
    for label in spec["uiCompletion"]["forbiddenUnsafeLabels"]:
        assert label not in combined_text
