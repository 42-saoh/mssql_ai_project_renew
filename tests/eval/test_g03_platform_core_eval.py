from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def test_g03_platform_core_eval_cases_are_declared():
    spec = _load_yaml("spec/development/fastapi_platform_core.yaml")

    for suite, expected_cases in spec["evalCases"].items():
        suite_spec = _load_yaml(f"spec/eval/{suite}.yaml")
        actual_cases = {case["id"] for case in suite_spec["cases"] if "id" in case}
        assert set(expected_cases) <= actual_cases
