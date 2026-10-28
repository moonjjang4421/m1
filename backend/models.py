from datetime import date as Date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DataCreate(BaseModel):
    date: Date
    value: float = Field(ge=0, le=1_000_000_000)
    memo: str = Field(default="", max_length=300)


class DataUpdate(BaseModel):
    date: Date | None = None
    value: float | None = Field(default=None, ge=0, le=1_000_000_000)
    memo: str | None = Field(default=None, max_length=300)

    @field_validator("memo")
    @classmethod
    def memo_not_none_when_present(cls, value: str | None) -> str | None:
        return value


class DataRecord(DataCreate):
    id: str


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=10_000)


class ConversationCreate(BaseModel):
    title: str = Field(default="새 대화", min_length=1, max_length=100)
    messages: list[Message] = Field(min_length=1, max_length=100)


class Conversation(ConversationCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    conversation_id: str | None = None
    messages: list[Message] = Field(default_factory=list, max_length=30)


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    summary: dict


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

