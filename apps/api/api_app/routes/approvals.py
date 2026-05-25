from __future__ import annotations

try:
    from fastapi import APIRouter
except Exception:
    APIRouter = None

from apps.api.api_app.services import approval_service

router = APIRouter() if APIRouter else None

if router:
    @router.get("/approvals")
    def list_approvals():
        return approval_service.list_approvals()

    @router.get("/approvals/{approvalId}")
    def get_approval(approvalId: str):
        return approval_service.get_approval(approvalId)

    @router.post("/approvals/{approvalId}/resume")
    def resume_approval(approvalId: str):
        return approval_service.resume_approval(approvalId)
