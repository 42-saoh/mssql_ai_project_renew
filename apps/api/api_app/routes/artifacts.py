from __future__ import annotations

try:
    from fastapi import APIRouter
    from pydantic import BaseModel
except Exception:
    APIRouter = None
    BaseModel = object

from apps.api.api_app.services import artifact_service

router = APIRouter() if APIRouter else None


class ValidatedArtifactPersistRequest(BaseModel):
    chatRunId: str = "manual"
    codexRunId: str | None = None
    proposal: dict


if router:
    @router.get("/artifacts")
    def list_artifacts():
        return artifact_service.list_artifacts()

    @router.post("/artifacts/validated")
    def persist_validated_artifact(req: ValidatedArtifactPersistRequest):
        payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
        return artifact_service.persist_validated_artifact_request(payload)

    @router.get("/artifacts/{artifactId}/validations")
    def list_artifact_validations(artifactId: str):
        return artifact_service.list_artifact_validations(artifactId)

    @router.get("/artifacts/{artifactId}")
    def get_artifact(artifactId: str):
        return artifact_service.get_artifact(artifactId)
