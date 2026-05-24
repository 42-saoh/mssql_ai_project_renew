from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "services/codex-runner/runtime-template"


def test_runtime_config_uses_never_approval_and_readonly_default():
    text = (RUNTIME / ".codex/config.toml").read_text(encoding="utf-8")
    assert 'approval_policy = "never"' in text
    assert 'sandbox_mode = "read-only"' in text
    assert 'model = "gpt-5.5"' in text
    assert 'model_reasoning_effort = "xhigh"' in text


def test_runtime_docs_do_not_authorize_root_skill_use():
    text = (RUNTIME / "SKILLS.md").read_text(encoding="utf-8")
    assert "Do not use root development skills" in text
