from __future__ import annotations

from plf_agent_orchestration.graph import orchestrate_message


def create_chat_run(message: str) -> dict[str, object]:
    return orchestrate_message(message)
