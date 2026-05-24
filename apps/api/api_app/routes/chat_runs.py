from __future__ import annotations

from uuid import uuid4

try:
    from fastapi import APIRouter
    from pydantic import BaseModel
except Exception:
    APIRouter = None
    BaseModel = object

from plf_agent_orchestration.graph import orchestrate_message

router = APIRouter() if APIRouter else None


class ChatRunCreate(BaseModel):
    conversationId: str | None = None
    message: str
    actorId: str | None = None


if router:
    @router.post("/chat-runs")
    def create_chat_run(req: ChatRunCreate):
        conversation_id = req.conversationId or f"conv_{uuid4().hex[:12]}"
        chat_run_id = f"chatrun_{uuid4().hex[:12]}"
        routed = orchestrate_message(req.message)
        return {
            "chatRunId": chat_run_id,
            "conversationId": conversation_id,
            "status": "ACCEPTED" if routed["policyDecision"] == "ALLOW" else "BLOCKED",
            **routed,
        }

    @router.get("/chat-runs/{chatRunId}")
    def get_chat_run(chatRunId: str):
        return {"chatRunId": chatRunId, "status": "SCAFFOLD"}

    @router.post("/chat-runs/{chatRunId}/resume")
    def resume_chat_run(chatRunId: str):
        return {"chatRunId": chatRunId, "status": "RESUMED"}
