from __future__ import annotations

try:
    from fastapi import APIRouter
except Exception:
    APIRouter = None

router = APIRouter() if APIRouter else None

if router:
    @router.get("/health")
    def health():
        return {"status": "ok", "service": "plf-db-agent-v2"}
