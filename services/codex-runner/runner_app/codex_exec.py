from __future__ import annotations

from pathlib import Path


def build_codex_exec_command(workspace: str | Path, output_schema: str = "schemas/output.schema.json") -> list[str]:
    return [
        "codex",
        "exec",
        "--cd",
        str(workspace),
        "--model",
        "gpt-5.5",
        "-c",
        'model_reasoning_effort="xhigh"',
        "--ask-for-approval",
        "never",
        "--sandbox",
        "read-only",
        "--json",
        "--output-last-message",
        "outputs/final.json",
        "--output-schema",
        output_schema,
        "Read AGENTS.md, input/run_request.json, input/evidence_bundle.json, and produce only schema-valid final JSON.",
    ]
