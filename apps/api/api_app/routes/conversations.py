from __future__ import annotations

try:
    from fastapi import APIRouter
except Exception:
    APIRouter = None

from apps.api.api_app.services import chat_service

router = APIRouter() if APIRouter else None

if router:
    @router.get("/conversations")
    def list_conversations():
        return chat_service.list_conversations()

    @router.get("/conversations/{conversationId}")
    def get_conversation(conversationId: str):
        return chat_service.get_conversation(conversationId)
