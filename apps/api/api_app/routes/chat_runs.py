from __future__ import annotations

try:
    from fastapi import APIRouter
    from pydantic import BaseModel
except Exception:
    APIRouter = None
    BaseModel = object

from apps.api.api_app.services import chat_service

router = APIRouter() if APIRouter else None


class ChatRunCreate(BaseModel):
    conversationId: str | None = None
    message: str
    actorId: str | None = None


if router:
    @router.post("/chat-runs")
    def create_chat_run(req: ChatRunCreate):
        return chat_service.create_chat_run(
            req.message,
            conversation_id=req.conversationId,
            actor_id=req.actorId,
        )

    @router.get("/chat-runs/{chatRunId}")
    def get_chat_run(chatRunId: str):
        return chat_service.get_chat_run(chatRunId)

    @router.post("/chat-runs/{chatRunId}/resume")
    def resume_chat_run(chatRunId: str):
        return chat_service.get_chat_run(chatRunId) | {"status": "RESUMED"}
