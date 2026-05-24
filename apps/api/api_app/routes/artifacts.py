from __future__ import annotations

try:
    from fastapi import APIRouter
except Exception:
    APIRouter = None

from apps.api.api_app.services import artifact_service

router = APIRouter() if APIRouter else None

if router:
    @router.get("/artifacts")
    def list_artifacts():
        return artifact_service.list_artifacts()

    @router.get("/artifacts/{artifactId}")
    def get_artifact(artifactId: str):
        return artifact_service.get_artifact(artifactId)
