from apps.api.api_app.settings import Settings, get_settings


STORE_ENV_KEYS = [
    "PLF_STORE_DB_DIALECT",
    "PLF_STORE_DB_HOST",
    "PLF_STORE_DB_PORT",
    "PLF_STORE_DB_NAME",
    "PLF_STORE_DB_USER",
    "PLF_STORE_DB_PASSWORD",
    "PLF_STORE_DB_DRIVER",
    "PLF_STORE_DB_ENCRYPT",
    "PLF_STORE_DB_TRUST_SERVER_CERTIFICATE",
    "PLF_STORE_SCHEMA_PATH",
    "PLF_STORE_AUTO_APPLY_SCHEMA",
]


def test_settings_platform_store_defaults_target_local_docker_mssql(monkeypatch):
    for key in STORE_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = get_settings()

    assert settings.store_db_dialect == "mssql"
    assert settings.store_db_host == "127.0.0.1"
    assert settings.store_db_port == 1433
    assert settings.store_db_name == "plf_db_agent_v2"
    assert settings.store_db_user == "sa"
    assert settings.store_db_password == ""
    assert settings.store_db_driver == "ODBC Driver 18 for SQL Server"
    assert settings.store_db_encrypt is False
    assert settings.store_db_trust_server_certificate is True
    assert settings.store_schema_path == "db/schema/plf_db_agent_v2.sql"
    assert settings.store_auto_apply_schema is False


def test_settings_platform_store_reads_env_overrides(monkeypatch):
    monkeypatch.setenv("PLF_STORE_DB_DIALECT", "mssql")
    monkeypatch.setenv("PLF_STORE_DB_HOST", "host.docker.internal")
    monkeypatch.setenv("PLF_STORE_DB_PORT", "11433")
    monkeypatch.setenv("PLF_STORE_DB_NAME", "custom_plf")
    monkeypatch.setenv("PLF_STORE_DB_USER", "plf_user")
    monkeypatch.setenv("PLF_STORE_DB_PASSWORD", "secret-value")
    monkeypatch.setenv("PLF_STORE_DB_DRIVER", "ODBC Driver 17 for SQL Server")
    monkeypatch.setenv("PLF_STORE_DB_ENCRYPT", "true")
    monkeypatch.setenv("PLF_STORE_DB_TRUST_SERVER_CERTIFICATE", "false")
    monkeypatch.setenv("PLF_STORE_SCHEMA_PATH", "/app/db/schema/plf_db_agent_v2.sql")
    monkeypatch.setenv("PLF_STORE_AUTO_APPLY_SCHEMA", "true")

    settings = get_settings()

    assert settings.store_db_host == "host.docker.internal"
    assert settings.store_db_port == 11433
    assert settings.store_db_name == "custom_plf"
    assert settings.store_db_user == "plf_user"
    assert settings.store_db_password == "secret-value"
    assert settings.store_db_driver == "ODBC Driver 17 for SQL Server"
    assert settings.store_db_encrypt is True
    assert settings.store_db_trust_server_certificate is False
    assert settings.store_schema_path == "/app/db/schema/plf_db_agent_v2.sql"
    assert settings.store_auto_apply_schema is True


def test_settings_repr_does_not_include_store_db_password():
    settings = Settings(store_db_password="secret-value")

    assert "secret-value" not in repr(settings)
