from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OrchestratorState:
    conversation_id: str
    chat_run_id: str
    actor_id: str
    sanitized_message_summary: str
    intent: str | None = None
    policy_decision: str | None = None
    target_key: str | None = None
    evidence_bundle_ref: str | None = None
    codex_run_id: str | None = None
    artifact_ids: list[str] = field(default_factory=list)
    review_markers: list[str] = field(default_factory=list)
    blocked_reason: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
