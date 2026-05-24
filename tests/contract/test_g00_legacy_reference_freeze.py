from pathlib import Path

import yaml

from plf_agent_contracts.enums import ArtifactType
from plf_agent_validation.policy_validator import ALLOWED_ARTIFACT_TYPES, RETIRED_ARTIFACT_TYPES

ROOT = Path(__file__).resolve().parents[2]
FREEZE_SPEC = ROOT / "spec/reference/legacy_reference_freeze.yaml"


def _freeze_spec() -> dict:
    return yaml.safe_load(FREEZE_SPEC.read_text(encoding="utf-8"))


def test_legacy_reference_docs_exist_and_forbid_copying():
    docs = [
        "docs/reference/legacy-reference-index.md",
        "docs/reference/legacy-policy-lessons.md",
        "docs/reference/legacy-artifact-taxonomy.md",
        "docs/reference/legacy-eval-lessons.md",
        "docs/reference/legacy-do-not-copy.md",
    ]
    for rel in docs:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert text
    assert "Do not copy" in (ROOT / "docs/reference/legacy-do-not-copy.md").read_text(encoding="utf-8")


def test_legacy_reference_freeze_contract_is_reference_only():
    spec = _freeze_spec()
    assert spec["status"] == "frozen_reference"
    assert spec["scope"]["legacy_material_status"] == "reference_only"
    assert spec["scope"]["v2_source_status"] == "greenfield"

    forbidden_ids = {item["id"] for item in spec["forbidden_uses"]}
    assert {
        "copy_implementation_modules",
        "runtime_dependency",
        "active_runtime_prompt_reuse",
        "realm_merge",
    } <= forbidden_ids


def test_legacy_artifact_taxonomy_matches_contracts_and_validator():
    spec = _freeze_spec()
    taxonomy = spec["artifact_taxonomy"]

    allowed = set(taxonomy["allowed_public_artifact_types"])
    assert allowed == {item.value for item in ArtifactType}
    assert allowed == ALLOWED_ARTIFACT_TYPES
    assert set(taxonomy["retired_public_artifact_types"]) == RETIRED_ARTIFACT_TYPES
    assert "TABLE_DESIGN_PREVIEW" in taxonomy["preview_only_artifact_types"]

    doc = (ROOT / "docs/reference/legacy-artifact-taxonomy.md").read_text(encoding="utf-8")
    for artifact_type in allowed | RETIRED_ARTIFACT_TYPES | {"TABLE_DESIGN_PREVIEW"}:
        assert artifact_type in doc


def test_legacy_policy_lessons_cover_required_boundaries():
    spec = _freeze_spec()
    policy_doc = (ROOT / "docs/reference/legacy-policy-lessons.md").read_text(encoding="utf-8").lower()
    root_policy = (ROOT / "POLICY.md").read_text(encoding="utf-8").lower()

    required_phrases = [
        "row-data query or display",
        "stored procedure execution",
        "free sql execution",
        "ddl or dml apply",
        "source apply",
        "deploy",
        "raw prompt persistence",
        "raw provider response persistence",
        "secret persistence",
        "general chatbot answers",
    ]
    for phrase in required_phrases:
        assert phrase in policy_doc

    for blocked in spec["policy_inheritance"]["blocked_operations"]:
        first_word = blocked.split()[1] if blocked.startswith("no ") else blocked.split()[0]
        first_word = first_word.lower()
        assert first_word in policy_doc or first_word in root_policy
