from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "services/codex-runner/runtime-template"


def test_legacy_implementation_tree_is_not_present_in_runtime_paths():
    implementation_roots = [
        ROOT / "apps",
        ROOT / "packages",
        ROOT / "services/codex-runner/runner_app",
        ROOT / "services/codex_runner",
    ]
    forbidden_names = {"legacy", "legacy_project", "legacy-app", "legacy_app"}

    for root in implementation_roots:
        for path in root.rglob("*"):
            parts = {part.lower() for part in path.relative_to(ROOT).parts}
            assert not (parts & forbidden_names)


def test_service_runtime_does_not_take_legacy_reference_docs_as_runtime_instructions():
    forbidden_reference_paths = [
        "docs/reference/legacy-reference-index.md",
        "docs/reference/legacy-policy-lessons.md",
        "docs/reference/legacy-artifact-taxonomy.md",
        "docs/reference/legacy-eval-lessons.md",
        "docs/reference/legacy-do-not-copy.md",
        "spec/reference/legacy_reference_freeze.yaml",
    ]

    for path in RUNTIME.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for forbidden in forbidden_reference_paths:
                assert forbidden not in text


def test_root_env_file_is_not_persisted_as_development_contract():
    assert not (ROOT / ".env").exists()
    assert (ROOT / ".env.example").exists()
