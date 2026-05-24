from __future__ import annotations

try:
    from fastapi import APIRouter
except Exception:
    APIRouter = None

router = APIRouter() if APIRouter else None

if router:
    @router.get("/artifacts")
    def list_artifacts():
        return {"items": []}

    @router.get("/artifacts/{artifactId}")
    def get_artifact(artifactId: str):
        return {"artifactId": artifactId, "status": "SCAFFOLD"}
