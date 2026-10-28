from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.database import Repository
from backend.dependencies import get_repository
from backend.models import Conversation, ConversationCreate

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=Conversation, status_code=status.HTTP_201_CREATED)
def save_conversation(payload: ConversationCreate, repo: Repository = Depends(get_repository)) -> dict:
    return repo.save_conversation(payload.model_dump(mode="json"))


@router.get("", response_model=list[Conversation])
def list_conversations(repo: Repository = Depends(get_repository)) -> list[dict]:
    """목록 응답에 전체 messages를 포함합니다."""
    return repo.list_conversations()


@router.get("/{conversation_id}", response_model=Conversation)
def get_conversation(conversation_id: str, repo: Repository = Depends(get_repository)) -> dict:
    conversation = repo.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, repo: Repository = Depends(get_repository)) -> Response:
    if not repo.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

