from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "services/codex-runner/runtime-template"

ROOT_DOCS = ["AGENTS.md", "POLICY.md", "PROJECT.md", "ARCHITECTURE.md", "EVAL_SPEC.md", "ROLES.md", "SKILLS.md", "TOOLS.md"]


def test_root_and_runtime_docs_exist():
    for name in ROOT_DOCS:
        assert (ROOT / name).exists(), name
        assert (RUNTIME / name).exists(), name


def test_runtime_declares_service_realm_not_development_realm():
    text = (RUNTIME / "AGENTS.md").read_text(encoding="utf-8")
    assert "Service Codex Runner Realm" in text
    assert "not the Development Codex" in text
    assert "root `.agents/skills`" in text


def test_runtime_skills_are_runtime_prefixed():
    skills_dir = RUNTIME / ".agents/skills"
    skill_names = [p.name for p in skills_dir.iterdir() if p.is_dir()]
    assert skill_names
    assert all(name.startswith("runtime-") for name in skill_names)


def test_development_docs_describe_separate_runtime_boundary():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Development Codex is not Service Codex Runner" in text
