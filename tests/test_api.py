# tests/test_api.py

import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealth:
    @pytest.mark.asyncio
    async def test_root(self, client):
        r = await client.get("/")
        assert r.status_code == 200
        assert "MAPA" in r.json()["name"]

    @pytest.mark.asyncio
    async def test_health(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestTasks:
    @pytest.mark.asyncio
    async def test_create_task(self, client):
        r = await client.post("/tasks", json={
            "title": "Test Task",
            "priority": "high",
            "user_id": "test_user"
        })
        assert r.status_code == 201
        assert r.json()["title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_list_tasks(self, client):
        r = await client.get("/tasks?user_id=test_user")
        assert r.status_code == 200
        assert "tasks" in r.json()

    @pytest.mark.asyncio
    async def test_create_and_get_task(self, client):
        create_r = await client.post("/tasks", json={
            "title": "Get Me Task",
            "user_id": "test_user"
        })
        task_id = create_r.json()["id"]
        r = await client.get(f"/tasks/{task_id}")
        assert r.status_code == 200
        assert r.json()["title"] == "Get Me Task"

    @pytest.mark.asyncio
    async def test_update_task(self, client):
        create_r = await client.post("/tasks", json={"title": "Update Me", "user_id": "test_user"})
        task_id = create_r.json()["id"]
        r = await client.patch(f"/tasks/{task_id}", json={"status": "done"})
        assert r.status_code == 200
        assert r.json()["status"] == "done"

    @pytest.mark.asyncio
    async def test_delete_task(self, client):
        create_r = await client.post("/tasks", json={"title": "Delete Me", "user_id": "test_user"})
        task_id = create_r.json()["id"]
        r = await client.delete(f"/tasks/{task_id}")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_task_not_found(self, client):
        r = await client.get("/tasks/nonexistent-id")
        assert r.status_code == 404


class TestEvents:
    @pytest.mark.asyncio
    async def test_create_event(self, client):
        r = await client.post("/events", json={
            "title": "Team Meeting",
            "event_date": "2025-08-15",
            "start_time": "14:00",
            "end_time": "15:00",
            "user_id": "test_user"
        })
        assert r.status_code == 201
        assert r.json()["title"] == "Team Meeting"

    @pytest.mark.asyncio
    async def test_list_events(self, client):
        r = await client.get("/events?user_id=test_user")
        assert r.status_code == 200
        assert "events" in r.json()


class TestNotes:
    @pytest.mark.asyncio
    async def test_create_note(self, client):
        r = await client.post("/notes", json={
            "title": "Test Note",
            "content": "This is test content.",
            "user_id": "test_user"
        })
        assert r.status_code == 201
        assert r.json()["title"] == "Test Note"

    @pytest.mark.asyncio
    async def test_list_notes(self, client):
        r = await client.get("/notes?user_id=test_user")
        assert r.status_code == 200
        assert "notes" in r.json()


class TestChat:
    @pytest.mark.asyncio
    async def test_chat_reset(self, client):
        r = await client.post("/chat/reset?user_id=test_user")
        assert r.status_code == 200