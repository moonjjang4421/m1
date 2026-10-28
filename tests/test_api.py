from datetime import date, timedelta


def add_records(client, count=6):
    start = date(2026, 1, 1)
    return [
        client.post("/api/data", json={"date": str(start + timedelta(days=i)), "value": 100 + i * 10, "memo": "test"}).json()
        for i in range(count)
    ]


def test_data_crud_and_summary(client):
    records = add_records(client)
    assert len(client.get("/api/data").json()) == 6

    updated = client.put(f"/api/data/{records[0]['id']}", json={"value": 250}).json()
    assert updated["value"] == 250

    summary = client.get("/api/data/summary").json()
    assert summary["count"] == 6
    assert summary["metrics"]["max"] == 250
    assert "trend" in summary

    assert client.delete(f"/api/data/{records[0]['id']}").status_code == 204
    assert len(client.get("/api/data").json()) == 5


def test_validation_rejects_negative_value(client):
    response = client.post("/api/data", json={"date": "2026-01-01", "value": -1, "memo": "invalid"})
    assert response.status_code == 422


def test_conversation_save_load_delete(client):
    payload = {"title": "테스트 대화", "messages": [{"role": "user", "content": "안녕"}]}
    created = client.post("/api/conversations", json=payload)
    assert created.status_code == 201
    conversation_id = created.json()["id"]
    assert client.get(f"/api/conversations/{conversation_id}").json()["messages"] == payload["messages"]
    assert client.delete(f"/api/conversations/{conversation_id}").status_code == 204
    assert client.get(f"/api/conversations/{conversation_id}").status_code == 404


def test_chat_injects_summary_and_auto_saves(client, monkeypatch):
    add_records(client)
    captured = {}

    def fake_ai(settings, summary, history, question):
        captured["summary"] = summary
        return f"평균은 {summary['metrics']['average']}입니다."

    monkeypatch.setattr("backend.routers.chat.ask_openai", fake_ai)
    response = client.post("/api/chat", json={"message": "평균은?", "messages": []})
    assert response.status_code == 200
    assert captured["summary"]["count"] == 6
    assert response.json()["conversation_id"]
    assert len(client.get("/api/conversations").json()) == 1

