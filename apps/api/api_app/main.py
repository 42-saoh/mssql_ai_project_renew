from __future__ import annotations

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover - allows contract tests without FastAPI installed
    FastAPI = None

from .routes import artifacts, chat_runs, health, metadata


def create_app():
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed")
    app = FastAPI(title="PLF DB Agent V2 API")
    app.include_router(health.router)
    app.include_router(chat_runs.router, prefix="/api/v1")
    app.include_router(artifacts.router, prefix="/api/v1")
    app.include_router(metadata.router, prefix="/api/v1")
    return app


app = create_app() if FastAPI is not None else None
