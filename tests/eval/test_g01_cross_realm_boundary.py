from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def test_g01_cross_realm_eval_cases_are_declared():
    contract = _load_yaml("spec/development/dual_codex_realm_contract.yaml")
    eval_spec = _load_yaml("spec/eval/v2_cross_realm_boundary.yaml")

    actual_case_ids = {case["id"] for case in eval_spec["cases"]}
    for case in contract["evalCases"]:
        assert case["suite"] == "v2_cross_realm_boundary"
        assert case["id"] in actual_case_ids
