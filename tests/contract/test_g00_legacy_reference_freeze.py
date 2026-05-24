from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_legacy_reference_docs_exist_and_forbid_copying():
    docs = [
        "docs/reference/legacy-reference-index.md",
        "docs/reference/legacy-policy-lessons.md",
        "docs/reference/legacy-artifact-taxonomy.md",
        "docs/reference/legacy-eval-lessons.md",
        "docs/reference/legacy-do-not-copy.md",
    ]
    for rel in docs:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert text
    assert "Do not copy" in (ROOT / "docs/reference/legacy-do-not-copy.md").read_text(encoding="utf-8")
