from __future__ import annotations

try:
    from fastapi import APIRouter
except Exception:
    APIRouter = None

from apps.api.api_app.services import approval_service

router = APIRouter() if APIRouter else None

if router:
    @router.post("/approvals/{approvalId}/resume")
    def resume_approval(approvalId: str):
        return approval_service.resume_approval(approvalId)
