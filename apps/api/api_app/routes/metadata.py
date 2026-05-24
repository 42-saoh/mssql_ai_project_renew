from __future__ import annotations

from typing import Any

try:
    from fastapi import APIRouter
    from pydantic import BaseModel, Field
except Exception:
    APIRouter = None
    BaseModel = object
    Field = None

from apps.api.api_app.services import metadata_service

router = APIRouter() if APIRouter else None


class ToolInvokeRequest(BaseModel):
    if Field is not None:
        arguments: dict[str, Any] = Field(default_factory=dict)


if router:
    @router.get("/metadata/ready")
    def metadata_ready():
        return metadata_service.metadata_ready()

    @router.get("/metadata/tools")
    def list_metadata_tools():
        return metadata_service.list_metadata_tools()

    @router.get("/metadata/db-profiles")
    def list_db_profiles():
        return metadata_service.list_db_profiles()

    @router.post("/metadata/tools/{toolName}/invoke")
    def invoke_metadata_tool(toolName: str, req: ToolInvokeRequest):
        return metadata_service.invoke_metadata_tool(toolName, getattr(req, "arguments", {}))

    @router.get("/metadata/search")
    def search_metadata(q: str, dbProfileId: str = "master", limit: int = 20):
        return metadata_service.search_metadata(q, db_profile_id=dbProfileId, limit=limit)
