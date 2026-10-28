import json
from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from uuid import uuid4

import firebase_admin
from firebase_admin import credentials, firestore

from backend.config import Settings
from backend.models import utcnow


class Repository(ABC):
    @abstractmethod
    def list_data(self) -> list[dict]: ...
    @abstractmethod
    def create_data(self, payload: dict) -> dict: ...
    @abstractmethod
    def update_data(self, record_id: str, payload: dict) -> dict | None: ...
    @abstractmethod
    def delete_data(self, record_id: str) -> bool: ...
    @abstractmethod
    def list_conversations(self) -> list[dict]: ...
    @abstractmethod
    def get_conversation(self, conversation_id: str) -> dict | None: ...
    @abstractmethod
    def save_conversation(self, payload: dict, conversation_id: str | None = None) -> dict: ...
    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool: ...


class MemoryRepository(Repository):
    def __init__(self) -> None:
        self.data: dict[str, dict] = {}
        self.conversations: dict[str, dict] = {}
        self.lock = Lock()

    def list_data(self) -> list[dict]:
        return sorted(self.data.values(), key=lambda row: row["date"])

    def create_data(self, payload: dict) -> dict:
        with self.lock:
            record = {"id": uuid4().hex, **payload}
            self.data[record["id"]] = record
            return record

    def update_data(self, record_id: str, payload: dict) -> dict | None:
        with self.lock:
            if record_id not in self.data:
                return None
            self.data[record_id].update(payload)
            return self.data[record_id]

    def delete_data(self, record_id: str) -> bool:
        with self.lock:
            return self.data.pop(record_id, None) is not None

    def list_conversations(self) -> list[dict]:
        return sorted(self.conversations.values(), key=lambda row: row["updated_at"], reverse=True)

    def get_conversation(self, conversation_id: str) -> dict | None:
        return self.conversations.get(conversation_id)

    def save_conversation(self, payload: dict, conversation_id: str | None = None) -> dict:
        with self.lock:
            now = utcnow()
            item_id = conversation_id or uuid4().hex
            existing = self.conversations.get(item_id)
            record = {
                "id": item_id,
                "title": payload["title"],
                "messages": payload["messages"],
                "created_at": existing["created_at"] if existing else now,
                "updated_at": now,
            }
            self.conversations[item_id] = record
            return record

    def delete_conversation(self, conversation_id: str) -> bool:
        with self.lock:
            return self.conversations.pop(conversation_id, None) is not None


class FirestoreRepository(Repository):
    def __init__(self, settings: Settings) -> None:
        if not firebase_admin._apps:
            if settings.firebase_service_account_json:
                cred = credentials.Certificate(json.loads(settings.firebase_service_account_json))
            elif settings.firebase_service_account_path:
                cred = credentials.Certificate(str(Path(settings.firebase_service_account_path)))
            else:
                cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    @staticmethod
    def _record(snapshot) -> dict:
        return {"id": snapshot.id, **(snapshot.to_dict() or {})}

    def list_data(self) -> list[dict]:
        return [self._record(doc) for doc in self.db.collection("data").order_by("date").stream()]

    def create_data(self, payload: dict) -> dict:
        ref = self.db.collection("data").document()
        ref.set(payload)
        return {"id": ref.id, **payload}

    def update_data(self, record_id: str, payload: dict) -> dict | None:
        ref = self.db.collection("data").document(record_id)
        if not ref.get().exists:
            return None
        ref.update(payload)
        return self._record(ref.get())

    def delete_data(self, record_id: str) -> bool:
        ref = self.db.collection("data").document(record_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True

    def list_conversations(self) -> list[dict]:
        query = self.db.collection("conversations").order_by("updated_at", direction=firestore.Query.DESCENDING)
        return [self._record(doc) for doc in query.stream()]

    def get_conversation(self, conversation_id: str) -> dict | None:
        doc = self.db.collection("conversations").document(conversation_id).get()
        return self._record(doc) if doc.exists else None

    def save_conversation(self, payload: dict, conversation_id: str | None = None) -> dict:
        ref = self.db.collection("conversations").document(conversation_id) if conversation_id else self.db.collection("conversations").document()
        current = ref.get()
        now = utcnow()
        record = {
            "title": payload["title"],
            "messages": payload["messages"],
            "created_at": current.to_dict().get("created_at", now) if current.exists else now,
            "updated_at": now,
        }
        ref.set(record)
        return {"id": ref.id, **record}

    def delete_conversation(self, conversation_id: str) -> bool:
        ref = self.db.collection("conversations").document(conversation_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True


def build_repository(settings: Settings) -> Repository:
    return MemoryRepository() if settings.use_memory_db else FirestoreRepository(settings)
