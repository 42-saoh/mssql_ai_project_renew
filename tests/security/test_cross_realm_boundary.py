from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "services/codex-runner/runtime-template"
CONTRACT = ROOT / "spec/development/dual_codex_realm_contract.yaml"


def _contract() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


def test_runtime_config_uses_never_approval_and_readonly_default():
    text = (RUNTIME / ".codex/config.toml").read_text(encoding="utf-8")
    assert 'approval_policy = "never"' in text
    assert 'sandbox_mode = "read-only"' in text
    assert 'model = "gpt-5.5"' in text
    assert 'model_reasoning_effort = "xhigh"' in text


def test_runtime_docs_do_not_authorize_root_skill_use():
    text = (RUNTIME / "SKILLS.md").read_text(encoding="utf-8")
    assert "Do not use root development skills" in text


def test_runtime_template_does_not_embed_development_skill_names():
    contract = _contract()
    runtime_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in RUNTIME.rglob("*")
        if path.is_file()
    )

    for skill_name in contract["developmentRealm"]["skills"]:
        assert skill_name not in runtime_text


def test_runtime_template_does_not_contain_credentials_or_root_path_imports():
    forbidden_patterns = [
        "CONTEXT7_API_KEY",
        "PGPT_API_KEY",
        "OPENAI_API_KEY",
        "PLF_DB_PASSWORD",
        "../.agents",
        "..\\.agents",
        "../.codex",
        "..\\.codex",
        "D:\\",
        "C:\\",
    ]
    runtime_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in RUNTIME.rglob("*")
        if path.is_file()
    )

    for pattern in forbidden_patterns:
        assert pattern not in runtime_text
