from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _env_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def test_db_schema_omits_forbidden_raw_payload_storage_fields():
    baseline = yaml.safe_load((ROOT / "spec/development/contract_schema_eval_baseline.yaml").read_text(encoding="utf-8"))
    sql = "\n".join(
        (ROOT / path).read_text(encoding="utf-8").lower()
        for path in [baseline["dbSchema"]["applyFile"], *baseline["dbSchema"]["migrationFiles"]]
    )

    for forbidden in baseline["dbSchema"]["forbiddenStorageFields"]:
        assert not re.search(rf"\b{re.escape(forbidden.lower())}\b", sql)


def test_db_schema_declares_validation_gate_storage_controls():
    baseline = yaml.safe_load((ROOT / "spec/development/contract_schema_eval_baseline.yaml").read_text(encoding="utf-8"))
    sql = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in [baseline["dbSchema"]["applyFile"], *baseline["dbSchema"]["migrationFiles"]])
    lowered = sql.lower()

    for table in baseline["dbSchema"]["requiredTables"]:
        assert f"create table dbo.{table}" in lowered

    for table, required_columns in baseline["dbSchema"]["requiredStorageControls"].items():
        assert f"CREATE TABLE dbo.{table}" in sql
        for column in required_columns:
            assert column in sql


def test_db_apply_schema_is_scoped_to_platform_storage_only():
    baseline = yaml.safe_load((ROOT / "spec/development/contract_schema_eval_baseline.yaml").read_text(encoding="utf-8"))
    sql = (ROOT / baseline["dbSchema"]["applyFile"]).read_text(encoding="utf-8")

    assert "Apply only to the PLF platform storage database" in sql
    assert "Do not apply this file to customer/business MSSQL databases" in sql
    assert "CREATE DATABASE" not in sql.upper()
    assert "USE " not in sql.upper()
    assert "CREATE TABLE IF NOT EXISTS" not in sql.upper()


def test_platform_store_env_targets_docker_mssql_without_committed_secret():
    baseline = yaml.safe_load((ROOT / "spec/development/contract_schema_eval_baseline.yaml").read_text(encoding="utf-8"))
    defaults = baseline["dbSchema"]["platformStoreEnv"]["defaults"]
    values = _env_values()

    assert values["PLF_STORE_DB_DIALECT"] == "mssql"
    assert values["PLF_STORE_DB_HOST"] == "127.0.0.1"
    assert values["PLF_STORE_DB_PORT"] == "1433"
    assert values["PLF_STORE_SCHEMA_PATH"] == baseline["dbSchema"]["applyFile"]
    assert values["PLF_STORE_AUTO_APPLY_SCHEMA"] == "false"
    assert values["PLF_STORE_DB_PASSWORD"] == defaults["PLF_STORE_DB_PASSWORD"] == ""
