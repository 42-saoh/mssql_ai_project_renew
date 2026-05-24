import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from plf_agent_contracts.enums import ArtifactType, Intent, RunStatus

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "spec/development/contract_schema_eval_baseline.yaml"


def _json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def _case_ids(cases: list[dict]) -> set[str]:
    return {case.get("id") or case.get("name") for case in cases}


def test_json_schemas_parse():
    for rel in [
        "spec/codex-runner/service_codex_run_request.schema.json",
        "spec/codex-runner/service_codex_run_result.schema.json",
        "spec/artifacts/sp_analysis_doc.schema.json",
        "spec/artifacts/dependency_report.schema.json",
        "spec/artifacts/table_design_preview.schema.json",
        "spec/artifacts/java_mybatis_draft_pack.schema.json",
    ]:
        assert json.loads((ROOT / rel).read_text(encoding="utf-8"))["$schema"]


def test_allowed_artifact_types_do_not_include_retired_types():
    schema = json.loads((ROOT / "spec/artifacts/sp_analysis_doc.schema.json").read_text(encoding="utf-8"))
    artifact_types = set(schema["properties"]["artifactType"]["enum"])
    assert "DDL_DRAFT" not in artifact_types
    assert "VO_DRAFT" not in artifact_types
    assert "MODEL_DRAFT" not in artifact_types
    assert "SP_ANALYSIS_DOC" in artifact_types


def test_g02_baseline_references_existing_contract_files():
    baseline = yaml.safe_load(BASELINE.read_text(encoding="utf-8"))

    assert (ROOT / baseline["openapi"]["path"]).exists()
    assert (ROOT / baseline["runnerSchemas"]["request"]["path"]).exists()
    assert (ROOT / baseline["runnerSchemas"]["result"]["path"]).exists()
    for path in baseline["artifactSchemas"]["paths"]:
        assert (ROOT / path).exists()
    for path in baseline["dbSchema"]["migrationFiles"]:
        assert (ROOT / path).exists()


def test_openapi_baseline_declares_required_paths_and_components():
    baseline = _yaml("spec/development/contract_schema_eval_baseline.yaml")
    openapi = _yaml(baseline["openapi"]["path"])

    assert openapi["openapi"] == "3.1.0"
    assert set(baseline["openapi"]["requiredPaths"]) <= set(openapi["paths"])

    schemas = openapi["components"]["schemas"]
    for schema_name in baseline["openapi"]["requiredSchemas"]:
        assert schema_name in schemas

    assert set(schemas["Intent"]["enum"]) == {item.value for item in Intent}
    assert set(schemas["ArtifactType"]["enum"]) == {item.value for item in ArtifactType}
    assert set(schemas["RunStatus"]["enum"]) == {item.value for item in RunStatus}


def test_json_schemas_are_valid_draft_2020_12_and_match_baseline_enums():
    baseline = _yaml("spec/development/contract_schema_eval_baseline.yaml")
    paths = [
        baseline["runnerSchemas"]["request"]["path"],
        baseline["runnerSchemas"]["result"]["path"],
        *baseline["artifactSchemas"]["paths"],
    ]

    for path in paths:
        Draft202012Validator.check_schema(_json(path))

    request_schema = _json(baseline["runnerSchemas"]["request"]["path"])
    result_schema = _json(baseline["runnerSchemas"]["result"]["path"])
    assert request_schema["properties"]["schemaVersion"]["const"] == baseline["runnerSchemas"]["request"]["schemaVersion"]
    assert set(request_schema["properties"]["runType"]["enum"]) == set(baseline["runnerSchemas"]["request"]["runTypes"])
    assert set(request_schema["properties"]["toolMode"]["enum"]) == set(baseline["runnerSchemas"]["request"]["toolModes"])
    assert result_schema["properties"]["schemaVersion"]["const"] == baseline["runnerSchemas"]["result"]["schemaVersion"]
    assert set(result_schema["properties"]["status"]["enum"]) == set(baseline["runnerSchemas"]["result"]["statuses"])
    assert result_schema["properties"]["productionReady"]["const"] is False


def test_artifact_schemas_match_allowed_and_retired_taxonomy():
    baseline = _yaml("spec/development/contract_schema_eval_baseline.yaml")
    allowed = set(baseline["artifactSchemas"]["allowedPublicArtifactTypes"])
    retired = set(baseline["artifactSchemas"]["retiredPublicArtifactTypes"])

    assert allowed == {item.value for item in ArtifactType}
    assert {"DDL_DRAFT", "VO_DRAFT", "MODEL_DRAFT"} == retired

    for path in baseline["artifactSchemas"]["paths"]:
        schema = _json(path)
        if "artifactType" in schema.get("properties", {}):
            enum = set(schema["properties"]["artifactType"]["enum"])
            assert allowed <= enum
            assert enum.isdisjoint(retired)
            for required in baseline["artifactSchemas"]["requiredArtifactFields"]:
                assert required in schema["required"]
            assert schema["properties"]["evidenceRefs"]["minItems"] == 1
            assert schema["properties"]["reviewMarkers"]["minItems"] == 1


def test_eval_baseline_declares_cases_for_all_required_suites():
    baseline = _yaml("spec/development/contract_schema_eval_baseline.yaml")
    eval_spec = (ROOT / "EVAL_SPEC.md").read_text(encoding="utf-8")

    for suite in baseline["evalBaseline"]["suites"]:
        assert suite in eval_spec
        suite_spec = _yaml(f"spec/eval/{suite}.yaml")
        assert suite_spec["name"] == suite
        assert suite_spec["cases"], suite

    for suite, expected_cases in baseline["evalBaseline"]["requiredCases"].items():
        actual_cases = _case_ids(_yaml(f"spec/eval/{suite}.yaml")["cases"])
        assert set(expected_cases) <= actual_cases
