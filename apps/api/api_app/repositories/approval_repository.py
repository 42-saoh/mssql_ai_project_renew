from __future__ import annotations

_STORE: dict[str, dict] = {}


def put(key: str, value: dict) -> dict:
    _STORE[key] = dict(value)
    return dict(_STORE[key])


def get(key: str) -> dict | None:
    value = _STORE.get(key)
    return dict(value) if value is not None else None


def list_all() -> list[dict]:
    return [dict(value) for value in _STORE.values()]


def clear() -> None:
    _STORE.clear()
