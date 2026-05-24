from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def _case_ids(cases: list[dict]) -> set[str]:
    return {case.get("id") or case.get("name") for case in cases}


def test_g02_eval_baseline_has_non_empty_suite_cases():
    baseline = _load_yaml("spec/development/contract_schema_eval_baseline.yaml")

    for suite in baseline["evalBaseline"]["suites"]:
        suite_spec = _load_yaml(f"spec/eval/{suite}.yaml")
        assert suite_spec["status"] == "scaffold"
        assert suite_spec["cases"], suite


def test_g02_required_eval_cases_are_declared_in_suite_specs():
    baseline = _load_yaml("spec/development/contract_schema_eval_baseline.yaml")

    for suite, expected_cases in baseline["evalBaseline"]["requiredCases"].items():
        suite_spec = _load_yaml(f"spec/eval/{suite}.yaml")
        assert set(expected_cases) <= _case_ids(suite_spec["cases"])
