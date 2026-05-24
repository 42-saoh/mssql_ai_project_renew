from pathlib import Path

import yaml

from runner_app.workspace import cleanup_workspace, create_workspace

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "spec/development/dual_codex_realm_contract.yaml"


def _contract() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


def test_runtime_workspace_is_created_from_runtime_template_only(tmp_path):
    contract = _contract()
    runtime = contract["serviceRuntimeRealm"]

    workspace = create_workspace(tmp_path, ROOT / runtime["root"])
    try:
        assert workspace.parent == tmp_path
        assert (workspace / "AGENTS.md").exists()
        assert (workspace / ".codex/config.toml").exists()
        assert (workspace / ".agents/skills").exists()
        for required_dir in contract["runtimeWorkspaceContract"]["requiredRuntimeDirs"]:
            assert (workspace / required_dir).is_dir()

        for forbidden in contract["runtimeWorkspaceContract"]["forbiddenCopiedFromRoot"]:
            assert not (workspace / forbidden).exists(), forbidden
    finally:
        cleanup_workspace(workspace)


def test_runtime_workspace_contains_runtime_skills_and_not_development_skills(tmp_path):
    contract = _contract()
    workspace = create_workspace(tmp_path, ROOT / contract["serviceRuntimeRealm"]["root"])
    try:
        runtime_skill_names = {p.name for p in (workspace / ".agents/skills").iterdir() if p.is_dir()}
        assert runtime_skill_names == set(contract["serviceRuntimeRealm"]["skills"])
        assert runtime_skill_names.isdisjoint(contract["developmentRealm"]["skills"])
    finally:
        cleanup_workspace(workspace)
