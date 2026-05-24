from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    environment: str = "dev"
    codex_runner_url: str = "http://localhost:8090"
    metadata_gateway_url: str = "http://localhost:8100"
    store_db_dialect: str = "mssql"
    store_db_host: str = "127.0.0.1"
    store_db_port: int = 1433
    store_db_name: str = "plf_db_agent_v2"
    store_db_user: str = "sa"
    store_db_password: str = field(default="", repr=False)
    store_db_driver: str = "ODBC Driver 18 for SQL Server"
    store_db_encrypt: bool = False
    store_db_trust_server_certificate: bool = True
    store_schema_path: str = "db/schema/plf_db_agent_v2.sql"
    store_auto_apply_schema: bool = False


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("PLF_ENVIRONMENT", "dev"),
        codex_runner_url=os.getenv("PLF_CODEX_RUNNER_URL", "http://localhost:8090"),
        metadata_gateway_url=os.getenv("PLF_METADATA_GATEWAY_URL", "http://localhost:8100"),
        store_db_dialect=os.getenv("PLF_STORE_DB_DIALECT", "mssql"),
        store_db_host=os.getenv("PLF_STORE_DB_HOST", "127.0.0.1"),
        store_db_port=_env_int("PLF_STORE_DB_PORT", 1433),
        store_db_name=os.getenv("PLF_STORE_DB_NAME", "plf_db_agent_v2"),
        store_db_user=os.getenv("PLF_STORE_DB_USER", "sa"),
        store_db_password=os.getenv("PLF_STORE_DB_PASSWORD", ""),
        store_db_driver=os.getenv("PLF_STORE_DB_DRIVER", "ODBC Driver 18 for SQL Server"),
        store_db_encrypt=_env_flag("PLF_STORE_DB_ENCRYPT", False),
        store_db_trust_server_certificate=_env_flag("PLF_STORE_DB_TRUST_SERVER_CERTIFICATE", True),
        store_schema_path=os.getenv("PLF_STORE_SCHEMA_PATH", "db/schema/plf_db_agent_v2.sql"),
        store_auto_apply_schema=_env_flag("PLF_STORE_AUTO_APPLY_SCHEMA", False),
    )
