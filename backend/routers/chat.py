from fastapi import APIRouter, Depends

from backend.config import Settings, get_settings
from backend.database import Repository
from backend.dependencies import get_repository
from backend.models import ChatRequest, ChatResponse
from backend.services.chat import ask_openai
from backend.services.summary import build_summary

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> dict:
    summary = build_summary(repo.list_data())
    history = [message.model_dump() for message in payload.messages]
    answer = ask_openai(settings, summary, history, payload.message)
    complete_messages = [*history, {"role": "user", "content": payload.message}, {"role": "assistant", "content": answer}]

    existing = repo.get_conversation(payload.conversation_id) if payload.conversation_id else None
    title = existing["title"] if existing else payload.message[:40]
    conversation = repo.save_conversation(
        {"title": title, "messages": complete_messages}, payload.conversation_id
    )
    return {"answer": answer, "conversation_id": conversation["id"], "summary": summary}

