from __future__ import annotations

_CHAT_RUNS: dict[str, dict] = {}
_CODEX_RUNS: dict[str, dict] = {}


def put(key: str, value: dict) -> dict:
    return put_chat_run(key, value)


def get(key: str) -> dict | None:
    return get_chat_run(key)


def put_chat_run(key: str, value: dict) -> dict:
    _CHAT_RUNS[key] = dict(value)
    return dict(_CHAT_RUNS[key])


def get_chat_run(key: str) -> dict | None:
    value = _CHAT_RUNS.get(key)
    return dict(value) if value is not None else None


def list_chat_runs() -> list[dict]:
    return [dict(value) for value in _CHAT_RUNS.values()]


def put_codex_run(key: str, value: dict) -> dict:
    _CODEX_RUNS[key] = dict(value)
    return dict(_CODEX_RUNS[key])


def get_codex_run(key: str) -> dict | None:
    value = _CODEX_RUNS.get(key)
    return dict(value) if value is not None else None


def list_codex_runs() -> list[dict]:
    return [dict(value) for value in _CODEX_RUNS.values()]


def clear() -> None:
    _CHAT_RUNS.clear()
    _CODEX_RUNS.clear()
