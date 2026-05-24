import json
import re
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


def _env_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


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
    assert (ROOT / baseline["dbSchema"]["applyFile"]).exists()
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


def test_db_apply_schema_declares_required_tables_and_is_executable():
    baseline = _yaml("spec/development/contract_schema_eval_baseline.yaml")
    apply_sql = (ROOT / baseline["dbSchema"]["applyFile"]).read_text(encoding="utf-8")
    migration_sql = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in baseline["dbSchema"]["migrationFiles"]
    )

    apply_tables = {
        name.lower()
        for name in re.findall(r"CREATE TABLE\s+dbo\.([A-Za-z_][A-Za-z0-9_]*)", apply_sql, flags=re.I)
    }
    migration_tables = {
        name.lower()
        for name in re.findall(r"CREATE TABLE\s+dbo\.([A-Za-z_][A-Za-z0-9_]*)", migration_sql, flags=re.I)
    }

    assert apply_tables == migration_tables == set(baseline["dbSchema"]["requiredTables"])
    assert "PLF platform storage database" in apply_sql
    assert "customer/business MSSQL" in apply_sql
    assert "CREATE TABLE IF NOT EXISTS" not in apply_sql.upper()
    for table in baseline["dbSchema"]["requiredTables"]:
        assert f"OBJECT_ID(N'dbo.{table}', N'U')" in apply_sql


def test_platform_store_env_contract_matches_example_and_apply_schema():
    baseline = _yaml("spec/development/contract_schema_eval_baseline.yaml")
    store_env = baseline["dbSchema"]["platformStoreEnv"]
    defaults = store_env["defaults"]
    values = _env_values()

    for key, expected in defaults.items():
        assert values[key] == expected

    assert defaults[store_env["schemaPathKey"]] == baseline["dbSchema"]["applyFile"]
    assert defaults[store_env["autoApplySchemaKey"]] == "false"
    assert store_env["autoApplySchemaDefaultAllowed"] is False
    assert store_env["customerDbCredentialsAllowed"] is False
    assert store_env["runtimeCredentialInheritanceAllowed"] is False
    assert defaults["PLF_STORE_DB_DIALECT"] == "mssql"
    assert defaults["PLF_STORE_DB_PORT"] == "1433"
    assert defaults["PLF_STORE_DB_PASSWORD"] == ""
