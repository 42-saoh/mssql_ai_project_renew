from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _spec() -> dict:
    return yaml.safe_load((ROOT / "spec/development/domain_feature_integration.yaml").read_text(encoding="utf-8"))


def test_g09_domain_feature_contract_files_exist():
    spec = _spec()

    assert spec["scope"] == "g09-domain-feature-integration"
    for path in spec["integrationSurfaces"].values():
        assert (ROOT / path).exists(), path


def test_g09_intent_flows_connect_to_allowed_boundaries():
    spec = _spec()
    flows = spec["intentFlows"]

    assert flows["METADATA_SEARCH"]["route"] == "metadata_gateway"
    assert flows["METADATA_SEARCH"]["externalTool"] == "search_metadata_objects"
    assert flows["METADATA_SEARCH"]["persistExternalResponse"] is False
    assert flows["HISTORY_LOOKUP"]["route"] == "history_store"
    assert flows["HISTORY_LOOKUP"]["returnsSanitizedSummariesOnly"] is True

    assert flows["SP_ANALYSIS"]["outputSchema"] == "schemas/sp_analysis_result.schema.json"
    assert flows["DEPENDENCY_ANALYSIS"]["outputSchema"] == "schemas/dependency_analysis_result.schema.json"
    assert flows["TABLE_DESIGN"]["outputSchema"] == "schemas/table_design_preview.schema.json"
    assert flows["DRAFT_GENERATION"]["outputSchema"] == "schemas/java_mybatis_draft_pack.schema.json"
    for intent in ["SP_ANALYSIS", "DEPENDENCY_ANALYSIS", "TABLE_DESIGN", "DRAFT_GENERATION"]:
        assert flows[intent]["route"] == "codex_runner"
        assert flows[intent]["runType"] == intent
        assert all(skill.startswith("runtime-") for skill in flows[intent]["skillAllowlist"])


def test_g09_contract_preserves_policy_boundaries():
    spec = _spec()
    policy = spec["policyBoundaries"]

    assert policy["streamlitCallsFastApiOnly"] is True
    assert policy["serviceRunnerReturnsProposalsOnly"] is True
    assert policy["validationGateControlsArtifactPersistence"] is True
    assert policy["rowDataAllowed"] is False
    assert policy["storedProcedureExecutionAllowed"] is False
    assert policy["freeSqlExecutionAllowed"] is False
    assert policy["ddlDmlApplyAllowed"] is False
    assert policy["sourceApplyAllowed"] is False
    assert policy["deployAllowed"] is False
    assert policy["rawPromptPersistenceAllowed"] is False
    assert policy["rawProviderResponsePersistenceAllowed"] is False
    assert policy["rawStoredProcedureDefinitionPersistenceAllowed"] is False
    assert policy["secretPersistenceAllowed"] is False
    assert policy["rootDevelopmentSkillsAllowedAtRuntime"] is False

