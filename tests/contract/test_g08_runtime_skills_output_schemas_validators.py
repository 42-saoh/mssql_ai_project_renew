from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "spec/development/runtime_skills_output_schemas_validators.yaml"


def _contract() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_g08_contract_files_and_runtime_skill_catalog_exist():
    contract = _contract()

    assert contract["scope"] == "g08-runtime-skills-output-schemas-validators"
    assert (ROOT / contract["runtimeTemplate"]["path"]).is_dir()
    assert (ROOT / contract["runtimeTemplate"]["skillsPath"]).is_dir()
    assert (ROOT / contract["runtimeTemplate"]["schemaRoot"]).is_dir()

    runtime_skill_dirs = {
        path.name
        for path in (ROOT / contract["runtimeTemplate"]["skillsPath"]).iterdir()
        if path.is_dir()
    }
    assert runtime_skill_dirs == set(contract["runtimeSkills"])

    for rel_path in contract["validators"].values():
        if isinstance(rel_path, str) and rel_path.endswith(".py"):
            assert (ROOT / rel_path).exists(), rel_path


def test_g08_runtime_skills_declare_service_scope_run_schema_and_artifacts():
    contract = _contract()

    for skill_name, skill in contract["runtimeSkills"].items():
        text = _read(skill["path"])
        assert skill_name.startswith("runtime-")
        assert "This is a Service Codex Runner skill" in text
        assert "not a Development Codex skill" in text

        if skill.get("validatorOnly"):
            assert "must not create domain content by itself" in text
            continue

        assert f"Allowed `runType`: `{skill['runType']}`" in text
        assert f"Required output schema: `{skill['outputSchema']}`" in text
        for artifact_type in skill["proposalArtifactTypes"]:
            assert artifact_type in text


def test_g08_runtime_output_schemas_are_valid_and_run_specific():
    contract = _contract()
    schema_root = ROOT / contract["runtimeTemplate"]["schemaRoot"]

    for schema_name in contract["outputSchemas"]["generic"]:
        schema_path = schema_root / schema_name.removeprefix("schemas/")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["properties"]["productionReady"]["const"] is False
        assert schema["properties"]["reviewRequired"]["const"] is True

    for run_type, schema_name in contract["outputSchemas"]["runSpecific"].items():
        schema_path = schema_root / schema_name.removeprefix("schemas/")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["properties"]["runType"]["const"] == run_type
        assert schema["properties"]["productionReady"]["const"] is False
        assert schema["properties"]["reviewRequired"]["const"] is True

        artifact_type_schema = schema["properties"]["artifactProposals"]["items"]["properties"]["artifactType"]
        expected_artifacts = next(
            skill["proposalArtifactTypes"]
            for skill in contract["runtimeSkills"].values()
            if skill.get("runType") == run_type
        )
        if "const" in artifact_type_schema:
            assert [artifact_type_schema["const"]] == expected_artifacts
        else:
            assert artifact_type_schema["enum"] == expected_artifacts


def test_g08_contract_preserves_policy_boundaries():
    contract = _contract()

    assert contract["runtimeTemplate"]["mustRemainServiceRealmOnly"] is True
    assert contract["validators"]["requestedOutputSchemaMustBeValidatedAfterCodexExec"] is True
    assert contract["validators"]["invalidOutputBehavior"].startswith("schema-valid BLOCKED")
    for key, value in contract["policyBoundaries"].items():
        if key == "runnerReturnsProposalsOnly":
            assert value is True
        else:
            assert value is False
