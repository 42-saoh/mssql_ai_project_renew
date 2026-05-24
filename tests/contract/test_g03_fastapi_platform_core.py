from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_g03_fastapi_platform_core_contract_files_exist():
    spec = yaml.safe_load((ROOT / "spec/development/fastapi_platform_core.yaml").read_text(encoding="utf-8"))

    for path in spec["apiBoundary"]["routeModules"]:
        assert (ROOT / path).exists(), path
    for path in spec["repositories"].values():
        assert (ROOT / path).exists(), path
    for path in spec["services"].values():
        assert (ROOT / path).exists(), path
    assert (ROOT / spec["settings"]["module"]).exists()


def test_g03_platform_core_contract_preserves_policy_controls():
    spec = yaml.safe_load((ROOT / "spec/development/fastapi_platform_core.yaml").read_text(encoding="utf-8"))
    controls = spec["persistenceControls"]

    assert controls["sanitizedChatSummaryOnly"] is True
    assert controls["rawUserMessageStored"] is False
    assert controls["rawPromptStored"] is False
    assert controls["rawProviderResponseStored"] is False
    assert controls["rowDataStored"] is False
    assert controls["secretsStored"] is False
    assert controls["validationRequiredBeforeArtifactPersistence"] is True
    assert controls["productionReadyArtifactPersistenceAllowed"] is False
    assert controls["artifactContentStoredInline"] is False


def test_g03_api_boundary_routes_are_declared_in_openapi():
    spec = yaml.safe_load((ROOT / "spec/development/fastapi_platform_core.yaml").read_text(encoding="utf-8"))
    openapi = yaml.safe_load((ROOT / spec["apiBoundary"]["openapiContract"]).read_text(encoding="utf-8"))

    for path in [
        "/health",
        "/api/v1/chat-runs",
        "/api/v1/conversations/{conversationId}",
        "/api/v1/artifacts",
        "/api/v1/metadata/search",
        "/api/v1/approvals/{approvalId}/resume",
    ]:
        assert path in openapi["paths"]


def test_g03_settings_contract_declares_safe_platform_store_env():
    spec = yaml.safe_load((ROOT / "spec/development/fastapi_platform_core.yaml").read_text(encoding="utf-8"))
    env = spec["settings"]["platformStoreEnv"]

    assert env["dialect"] == "PLF_STORE_DB_DIALECT"
    assert env["host"] == "PLF_STORE_DB_HOST"
    assert env["port"] == "PLF_STORE_DB_PORT"
    assert env["name"] == "PLF_STORE_DB_NAME"
    assert env["password"] == "PLF_STORE_DB_PASSWORD"
    assert env["schemaPath"] == "PLF_STORE_SCHEMA_PATH"
    assert env["autoApplySchema"] == "PLF_STORE_AUTO_APPLY_SCHEMA"
    assert spec["settings"]["storeAutoApplySchemaDefault"] is False
    assert spec["settings"]["storePasswordReprAllowed"] is False
