from __future__ import annotations


def require_actor_id(actor_id: str | None = None) -> str:
    return actor_id or "dev-user"
