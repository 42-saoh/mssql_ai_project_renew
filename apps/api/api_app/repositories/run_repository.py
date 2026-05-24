from __future__ import annotations

_STORE: dict[str, dict] = {}


def put(key: str, value: dict) -> dict:
    _STORE[key] = dict(value)
    return _STORE[key]


def get(key: str) -> dict | None:
    return _STORE.get(key)
