import json
import subprocess
from pathlib import Path

import pytest

from runner_app.event_parser import parse_jsonl_events, summarize_event_stream
from runner_app.real_runner import RealRunnerConfig, submit_real_run
from runner_app.workspace import WorkspaceContractError, cleanup_workspace, create_workspace, write_run_inputs

ROOT = Path(__file__).resolve().parents[3]
RUNTIME_TEMPLATE = ROOT / "services/codex-runner/runtime-template"


def _request() -> dict:
    return {
        "schemaVersion": "ServiceCodexRunRequest.v1",
        "runType": "SP_ANALYSIS",
        "chatRunId": "chat-1",
        "conversationId": "conv-1",
        "target": {
            "dbProfileId": "profile-1",
            "objectType": "PROCEDURE",
            "schema": "dbo",
            "name": "InvoiceAudit",
            "targetKey": "profile-1.PROCEDURE.dbo.InvoiceAudit",
        },
        "policy": {
            "allowRowData": False,
            "allowProcedureExecution": False,
            "allowDdlDmlApply": False,
            "allowSourceApply": False,
            "allowDeploy": False,
            "allowRawPromptStorage": False,
            "allowRawProviderResponseStorage": False,
        },
        "toolMode": "EVIDENCE_BUNDLE_ONLY",
        "skillAllowlist": ["runtime-sp-analysis", "runtime-output-validation"],
        "outputSchema": "service_codex_run_result.schema.json",
        "evidenceBundleRef": "evidence.bundle.1",
    }


def _valid_result() -> dict:
    return {
        "schemaVersion": "ServiceCodexRunResult.v1",
        "runType": "SP_ANALYSIS",
        "targetKey": "profile-1.PROCEDURE.dbo.InvoiceAudit",
        "status": "SUCCEEDED",
        "productionReady": False,
        "reviewRequired": True,
        "artifactProposals": [
            {
                "artifactType": "SP_ANALYSIS_DOC",
                "title": "Invoice audit analysis",
                "contentMarkdown": "REVIEW_REQUIRED draft based on sanitized metadata evidence.",
                "evidenceRefs": ["evidence.bundle.1"],
                "reviewMarkers": ["REVIEW_REQUIRED"],
            }
        ],
        "blockers": [],
        "validation": {"schemaValid": True, "policyValid": True, "staticValidationPassed": True},
    }


def test_workspace_creation_rejects_development_root_as_runtime_template(tmp_path):
    with pytest.raises(WorkspaceContractError):
        create_workspace(tmp_path, ROOT)


def test_workspace_creation_copies_runtime_template_and_writes_inputs(tmp_path):
    workspace = create_workspace(tmp_path, RUNTIME_TEMPLATE)
    try:
        assert workspace.name.startswith("codexrun_")
        assert (workspace / "AGENTS.md").read_text(encoding="utf-8").startswith("# Service Codex Runner Realm")
        assert (workspace / ".agents/skills").is_dir()
        assert not (workspace / "goals").exists()
        assert not (workspace / "README.md").exists()

        write_run_inputs(workspace, _request(), {"evidenceRefs": ["evidence.bundle.1"]})

        assert json.loads((workspace / "input/run_request.json").read_text(encoding="utf-8"))["runType"] == "SP_ANALYSIS"
        assert json.loads((workspace / "input/evidence_bundle.json").read_text(encoding="utf-8"))["evidenceRefs"] == [
            "evidence.bundle.1"
        ]
        assert not (workspace / "input/tool_catalog.json").exists()
    finally:
        cleanup_workspace(workspace)


def test_event_parser_keeps_only_safe_summary_fields():
    stdout = "\n".join(
        [
            json.dumps({"type": "task_started", "content": "raw provider response should not be summarized"}),
            "not json",
            json.dumps({"type": "turn_completed", "message": "raw prompt should not be summarized"}),
        ]
    )

    events = parse_jsonl_events(stdout.splitlines())
    summary = summarize_event_stream(stdout, "provider stderr line")

    assert events[1]["type"] == "unparsed"
    assert "content" not in events[0]
    assert "message" not in events[2]
    assert summary == {
        "eventCount": 3,
        "eventTypes": ["task_started", "turn_completed", "unparsed"],
        "unparsedCount": 1,
        "stderrLineCount": 1,
    }
    assert "raw provider" not in json.dumps(summary)
    assert "raw prompt" not in json.dumps(summary)


def test_submit_real_run_materializes_workspace_runs_codex_and_validates_output(tmp_path):
    workspaces = tmp_path / "workspaces"

    def fake_codex(command, **kwargs):
        workspace = Path(command[command.index("--cd") + 1])
        assert command[command.index("--sandbox") + 1] == "read-only"
        assert command[command.index("--ask-for-approval") + 1] == "never"
        assert command[command.index("--output-schema") + 1] == "schemas/service_codex_run_result.schema.json"
        assert json.loads((workspace / "input/run_request.json").read_text(encoding="utf-8"))["runType"] == "SP_ANALYSIS"
        (workspace / "outputs/final.json").write_text(json.dumps(_valid_result()), encoding="utf-8")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"type": "turn_completed", "content": "provider content is excluded"}) + "\n",
            stderr="",
        )

    result = submit_real_run(
        _request(),
        {"evidenceRefs": ["evidence.bundle.1"]},
        config=RealRunnerConfig(workspace_base=workspaces, runtime_template=RUNTIME_TEMPLATE),
        run_command=fake_codex,
    )

    assert result["status"] == "SUCCEEDED"
    assert result["validation"] == {"schemaValid": True, "policyValid": True, "staticValidationPassed": True}
    assert result["artifactProposals"][0]["artifactType"] == "SP_ANALYSIS_DOC"
    assert result["runtime"]["eventTypes"] == ["turn_completed"]
    assert result["runtime"]["returnCode"] == 0
    assert not any(workspaces.iterdir())
    assert "provider content" not in json.dumps(result)


def test_submit_real_run_blocks_unsafe_inputs_before_codex_exec(tmp_path):
    called = False
    request = _request()
    request["policy"]["allowDeploy"] = True

    def fake_codex(command, **kwargs):
        nonlocal called
        called = True
        return subprocess.CompletedProcess(command, 0)

    result = submit_real_run(
        request,
        {"evidenceRefs": ["evidence.bundle.1"]},
        config=RealRunnerConfig(workspace_base=tmp_path, runtime_template=RUNTIME_TEMPLATE),
        run_command=fake_codex,
    )

    assert result["status"] == "BLOCKED"
    assert not result["artifactProposals"]
    assert any("allowDeploy" in blocker for blocker in result["blockers"])
    assert called is False


def test_submit_real_run_blocks_row_data_evidence_before_codex_exec(tmp_path):
    called = False

    def fake_codex(command, **kwargs):
        nonlocal called
        called = True
        return subprocess.CompletedProcess(command, 0)

    result = submit_real_run(
        _request(),
        {"data": {"rows": [{"customer": "alice"}]}},
        config=RealRunnerConfig(workspace_base=tmp_path, runtime_template=RUNTIME_TEMPLATE),
        run_command=fake_codex,
    )

    serialized = json.dumps(result)
    assert result["status"] == "BLOCKED"
    assert result["artifactProposals"] == []
    assert "ROW_DATA" in result["blockers"]
    assert "alice" not in serialized
    assert called is False


@pytest.mark.parametrize(
    ("evidence_bundle", "violation"),
    [
        ({"procedureDefinition": "AS BEGIN SELECT 1 END"}, "RAW_SP"),
        ({"definition": "AS BEGIN SELECT 1 END"}, "RAW_SP"),
        ({"diagnostics": "Server=tcp:prod;Database=ERP;Integrated Security=True;"}, "CONNECTION_STRING"),
    ],
)
def test_submit_real_run_blocks_raw_sp_and_connection_string_inputs_before_codex_exec(
    tmp_path, evidence_bundle, violation
):
    called = False

    def fake_codex(command, **kwargs):
        nonlocal called
        called = True
        return subprocess.CompletedProcess(command, 0)

    result = submit_real_run(
        _request(),
        evidence_bundle,
        config=RealRunnerConfig(workspace_base=tmp_path, runtime_template=RUNTIME_TEMPLATE),
        run_command=fake_codex,
    )

    serialized = json.dumps(result)
    assert result["status"] == "BLOCKED"
    assert result["artifactProposals"] == []
    assert violation in result["blockers"]
    assert "server=" not in serialized.lower()
    assert "select 1" not in serialized.lower()
    assert called is False


@pytest.mark.parametrize("status", ["FAILED", "BLOCKED"])
def test_submit_real_run_strips_proposals_from_failed_or_blocked_outputs(tmp_path, status):
    def fake_codex(command, **kwargs):
        workspace = Path(command[command.index("--cd") + 1])
        result = _valid_result()
        result["status"] = status
        result["blockers"] = [f"UPSTREAM_{status}"]
        (workspace / "outputs/final.json").write_text(json.dumps(result), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = submit_real_run(
        _request(),
        {"evidenceRefs": ["evidence.bundle.1"]},
        config=RealRunnerConfig(workspace_base=tmp_path, runtime_template=RUNTIME_TEMPLATE),
        run_command=fake_codex,
    )

    assert result["status"] == "BLOCKED"
    assert result["artifactProposals"] == []
    assert f"ARTIFACT_PROPOSALS_NOT_ALLOWED_FOR_STATUS:{status}" in result["blockers"]
    assert result["validation"]["schemaValid"] is True
    assert result["validation"]["policyValid"] is False
    assert result["validation"]["staticValidationPassed"] is False


def test_submit_real_run_returns_safe_blocked_envelope_for_unsafe_output(tmp_path):
    def fake_codex(command, **kwargs):
        workspace = Path(command[command.index("--cd") + 1])
        result = _valid_result()
        result["artifactProposals"][0]["contentMarkdown"] = "raw prompt: summarize this secret"
        (workspace / "outputs/final.json").write_text(json.dumps(result), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = submit_real_run(
        _request(),
        {"evidenceRefs": ["evidence.bundle.1"]},
        config=RealRunnerConfig(workspace_base=tmp_path, runtime_template=RUNTIME_TEMPLATE),
        run_command=fake_codex,
    )

    serialized = json.dumps(result)
    assert result["status"] == "BLOCKED"
    assert result["artifactProposals"] == []
    assert "RAW_PROMPT" in result["blockers"]
    assert "raw prompt" not in serialized
    assert "summarize this secret" not in serialized


def test_submit_real_run_returns_safe_blocked_envelope_for_raw_sp_output(tmp_path):
    def fake_codex(command, **kwargs):
        workspace = Path(command[command.index("--cd") + 1])
        result = _valid_result()
        result["debug"] = {"definition": "AS BEGIN SELECT 1 END"}
        (workspace / "outputs/final.json").write_text(json.dumps(result), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = submit_real_run(
        _request(),
        {"evidenceRefs": ["evidence.bundle.1"]},
        config=RealRunnerConfig(workspace_base=tmp_path, runtime_template=RUNTIME_TEMPLATE),
        run_command=fake_codex,
    )

    serialized = json.dumps(result)
    assert result["status"] == "BLOCKED"
    assert result["artifactProposals"] == []
    assert "RAW_SP" in result["blockers"]
    assert "select 1" not in serialized.lower()


def test_submit_real_run_returns_safe_blocked_envelope_for_row_data_output(tmp_path):
    def fake_codex(command, **kwargs):
        workspace = Path(command[command.index("--cd") + 1])
        result = _valid_result()
        result["debug"] = {"records": [{"customer": "alice"}]}
        (workspace / "outputs/final.json").write_text(json.dumps(result), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = submit_real_run(
        _request(),
        {"evidenceRefs": ["evidence.bundle.1"]},
        config=RealRunnerConfig(workspace_base=tmp_path, runtime_template=RUNTIME_TEMPLATE),
        run_command=fake_codex,
    )

    serialized = json.dumps(result)
    assert result["status"] == "BLOCKED"
    assert result["artifactProposals"] == []
    assert "ROW_DATA" in result["blockers"]
    assert "alice" not in serialized


def test_submit_real_run_returns_safe_blocked_envelope_when_final_output_missing(tmp_path):
    def fake_codex(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="warning line")

    result = submit_real_run(
        _request(),
        {"evidenceRefs": ["evidence.bundle.1"]},
        config=RealRunnerConfig(workspace_base=tmp_path, runtime_template=RUNTIME_TEMPLATE),
        run_command=fake_codex,
    )

    assert result["status"] == "BLOCKED"
    assert result["artifactProposals"] == []
    assert "MISSING_FINAL_OUTPUT" in result["blockers"]
    assert result["runtime"]["stderrLineCount"] == 1
