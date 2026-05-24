from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import Intent, RunStatus


@dataclass(frozen=True)
class ChatRunRequest:
    conversation_id: str | None
    message: str
    actor_id: str


@dataclass(frozen=True)
class ChatRunResponse:
    chat_run_id: str
    conversation_id: str
    intent: Intent
    status: RunStatus
    message: str
    artifacts: list[dict[str, Any]] = field(default_factory=list)
