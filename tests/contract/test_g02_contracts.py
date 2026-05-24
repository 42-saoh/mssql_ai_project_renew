import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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
