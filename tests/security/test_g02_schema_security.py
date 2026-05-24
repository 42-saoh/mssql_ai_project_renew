from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_db_schema_omits_forbidden_raw_payload_storage_fields():
    baseline = yaml.safe_load((ROOT / "spec/development/contract_schema_eval_baseline.yaml").read_text(encoding="utf-8"))
    sql = "\n".join(
        (ROOT / path).read_text(encoding="utf-8").lower()
        for path in baseline["dbSchema"]["migrationFiles"]
    )

    for forbidden in baseline["dbSchema"]["forbiddenStorageFields"]:
        assert not re.search(rf"\b{re.escape(forbidden.lower())}\b", sql)


def test_db_schema_declares_validation_gate_storage_controls():
    baseline = yaml.safe_load((ROOT / "spec/development/contract_schema_eval_baseline.yaml").read_text(encoding="utf-8"))
    sql = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in baseline["dbSchema"]["migrationFiles"])
    lowered = sql.lower()

    for table in baseline["dbSchema"]["requiredTables"]:
        assert f"create table {table}" in lowered

    for table, required_columns in baseline["dbSchema"]["requiredStorageControls"].items():
        assert f"CREATE TABLE {table}" in sql
        for column in required_columns:
            assert column in sql
