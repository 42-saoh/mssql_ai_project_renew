from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "spec/development/service_codex_runner_foundation.yaml"


def _contract() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


def test_g07_contract_declares_runner_foundation_boundaries():
    contract = _contract()

    assert contract["service"] == "serviceCodexRunnerFoundation"
    assert contract["scope"] == "g07-service-codex-runner-foundation"
    assert contract["runtimeTemplate"]["path"] == "services/codex-runner/runtime-template"
    assert contract["runtimeTemplate"]["canonicalOnly"] is True
    assert contract["runtimeTemplate"]["alternateMarkerCompliantTemplatesAllowed"] is False
    assert contract["runtimeTemplate"]["requiredMarker"] == "Service Codex Runner Realm"
    assert contract["workspace"]["createdBy"] == "services/codex-runner/runner_app/workspace.py"
    assert contract["workspace"]["symlinksAllowed"] is False
    assert contract["codexExec"]["approvalPolicy"] == "never"
    assert contract["codexExec"]["sandboxMode"] == "read-only"
    assert contract["codexExec"]["outputSchemaRoot"] == "schemas"


def test_g07_contract_referenced_files_exist():
    contract = _contract()
    runtime_root = ROOT / contract["runtimeTemplate"]["path"]

    for rel_path in contract["runtimeTemplate"]["requiredPaths"]:
        assert (runtime_root / rel_path).exists(), rel_path

    for rel_path in [
        contract["workspace"]["createdBy"],
        contract["codexExec"]["commandBuilder"],
        contract["eventParsing"]["parser"],
        contract["validation"]["validator"],
        contract["validation"]["sanitizer"],
        contract["validation"]["outputSchema"],
        contract["inputs"]["requestSchema"],
    ]:
        assert (ROOT / rel_path).exists(), rel_path


def test_g07_contract_blocks_raw_events_and_runtime_persistence():
    contract = _contract()

    assert contract["eventParsing"]["persistRawStdout"] is False
    assert contract["eventParsing"]["persistRawStderr"] is False
    assert contract["eventParsing"]["persistRawModelContent"] is False
    assert contract["validation"]["invalidOutputBehavior"].startswith("schema-valid BLOCKED")
    assert contract["validation"]["blockedEnvelopeBlockersSanitized"] is True
    assert contract["validation"]["proposalStatusesAllowed"] == ["SUCCEEDED", "REVIEW_REQUIRED"]
    assert contract["validation"]["failedOrBlockedOutputBehavior"].startswith("schema-valid BLOCKED")
    assert contract["policyBoundaries"]["runnerReturnsProposalsOnly"] is True
    assert contract["policyBoundaries"]["artifactPersistenceAllowedInRunner"] is False
    assert contract["policyBoundaries"]["rootDevelopmentSkillsAllowedAtRuntime"] is False
    for key in [
        "rowDataAllowed",
        "procedureExecutionAllowed",
        "ddlDmlApplyAllowed",
        "sourceApplyAllowed",
        "deployAllowed",
    ]:
        assert contract["policyBoundaries"][key] is False
