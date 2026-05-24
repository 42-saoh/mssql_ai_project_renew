from pathlib import Path
import tomllib

import yaml

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "services/codex-runner/runtime-template"
CONTRACT_PATH = ROOT / "spec/development/dual_codex_realm_contract.yaml"

ROOT_DOCS = ["AGENTS.md", "POLICY.md", "PROJECT.md", "ARCHITECTURE.md", "EVAL_SPEC.md", "ROLES.md", "SKILLS.md", "TOOLS.md"]


def _contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def _toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _resolve_dotted(data: dict, key: str):
    current = data
    for part in key.split("."):
        current = current[part]
    return current


def _skill_dirs(path: Path) -> set[str]:
    return {p.name for p in path.iterdir() if p.is_dir()}


def _agent_names(path: Path) -> set[str]:
    return {p.stem for p in path.glob("*.toml")}


def test_root_and_runtime_docs_exist():
    contract = _contract()
    assert contract["developmentRealm"]["docs"] == ROOT_DOCS
    assert contract["serviceRuntimeRealm"]["docs"] == ROOT_DOCS

    for name in contract["developmentRealm"]["docs"]:
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


def test_dual_realm_contract_matches_actual_configs_agents_and_skills():
    contract = _contract()
    dev = contract["developmentRealm"]
    runtime = contract["serviceRuntimeRealm"]

    assert _agent_names(ROOT / dev["agentsPath"]) == set(dev["agents"])
    assert _agent_names(ROOT / runtime["agentsPath"]) == set(runtime["agents"])
    assert _skill_dirs(ROOT / dev["skillsPath"]) == set(dev["skills"])
    assert _skill_dirs(ROOT / runtime["skillsPath"]) == set(runtime["skills"])

    dev_config = _toml(ROOT / dev["config"])
    runtime_config = _toml(ROOT / runtime["config"])
    for key, expected in dev["configExpectations"].items():
        assert _resolve_dotted(dev_config, key) == expected
    for key, expected in runtime["configExpectations"].items():
        assert _resolve_dotted(runtime_config, key) == expected


def test_skill_catalog_docs_match_filesystem_contract():
    contract = _contract()
    dev_skills_doc = (ROOT / "SKILLS.md").read_text(encoding="utf-8")
    runtime_skills_doc = (RUNTIME / "SKILLS.md").read_text(encoding="utf-8")

    for skill in contract["developmentRealm"]["skills"]:
        assert skill in dev_skills_doc
        assert skill not in runtime_skills_doc
    for skill in contract["serviceRuntimeRealm"]["skills"]:
        assert skill in runtime_skills_doc
        assert skill not in dev_skills_doc


def test_agents_are_bound_to_their_own_realm():
    contract = _contract()

    for agent_file in (ROOT / contract["developmentRealm"]["agentsPath"]).glob("*.toml"):
        agent = _toml(agent_file)
        assert "Development Codex Realm" in agent["developer_instructions"]
        assert "Service Codex Runner Realm" not in agent["developer_instructions"]

    for agent_file in (ROOT / contract["serviceRuntimeRealm"]["agentsPath"]).glob("*.toml"):
        agent = _toml(agent_file)
        assert agent["profile"].startswith("runtime-")
        assert "Service Codex Runner Realm" in agent["instructions"]["summary"]


def test_boundary_contract_forbids_shared_realm_state():
    rules = _contract()["boundaryRules"]

    assert rules["docsShared"] is False
    assert rules["configsShared"] is False
    assert rules["agentsShared"] is False
    assert rules["skillsShared"] is False
    assert rules["workspacesShared"] is False
    assert rules["credentialsShared"] is False
    assert rules["auditBoundariesShared"] is False
    assert rules["runtimeCanReadRootDevelopmentSkills"] is False
    assert rules["runtimeCanInheritRootDevelopmentDocs"] is False
    assert rules["runtimeTemplateCanContainSecrets"] is False
