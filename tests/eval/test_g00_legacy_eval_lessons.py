from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def test_legacy_eval_lessons_are_mapped_to_eval_suite_cases():
    freeze = _load_yaml("spec/reference/legacy_reference_freeze.yaml")

    by_suite: dict[str, set[str]] = {}
    for lesson in freeze["eval_lessons"]:
        by_suite.setdefault(lesson["suite"], set()).add(lesson["case_id"])

    for suite, expected_case_ids in by_suite.items():
        suite_spec = _load_yaml(f"spec/eval/{suite}.yaml")
        actual_case_ids = {case["id"] for case in suite_spec["cases"]}
        assert expected_case_ids <= actual_case_ids


def test_legacy_eval_doc_names_all_mapped_suites():
    freeze = _load_yaml("spec/reference/legacy_reference_freeze.yaml")
    doc = (ROOT / "docs/reference/legacy-eval-lessons.md").read_text(encoding="utf-8")

    for lesson in freeze["eval_lessons"]:
        assert lesson["suite"] in doc
