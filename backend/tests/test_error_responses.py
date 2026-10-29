import os
import sys

import asyncpg
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters")

SECRET_DETAIL = "relation users at /srv/db password=hunter2"

BODY = dict(age=50, gender="male", height=175, weight=80, bloodPressure="130/85", heartRate=72,
            physicalActivity="moderate", sleepHours=7, smokingHabit="no")


class FakeDAL:
    async def get_user_by_email(self, email):
        return {"id": 1, "name": "U", "email": email}

    async def create_health_record(self, **kwargs):
        # asyncpg's DataError subclasses ValueError, so it must not be mistaken for a validation error
        raise asyncpg.exceptions.DataError(SECRET_DETAIL)


@pytest.fixture
def server_client():
    import server
    from fastapi.testclient import TestClient

    server.app.state.dal = FakeDAL()
    token = server.create_access_token({"sub": "u@example.com", "user_id": 1})
    return server, TestClient(server.app), {"Authorization": f"Bearer {token}"}


def assert_hidden(response, status_code):
    assert response.status_code == status_code
    assert SECRET_DETAIL not in response.text
    assert "Please try again" in response.json()["detail"]


def test_unexpected_prediction_error_is_hidden(server_client, monkeypatch):
    server, client, _ = server_client

    def boom(_):
        raise RuntimeError(SECRET_DETAIL)
    monkeypatch.setattr(server, "run_assessment", boom)
    assert_hidden(client.post("/api/predict", json=BODY), 500)


def test_validation_message_from_risk_model_is_shown(server_client, monkeypatch):
    server, client, _ = server_client

    def invalid(_):
        raise ValueError("Height and weight are required to compute BMI")
    monkeypatch.setattr(server, "run_assessment", invalid)
    r = client.post("/api/predict", json=BODY)
    assert r.status_code == 422
    assert r.json()["detail"] == "Height and weight are required to compute BMI"


def test_database_error_is_hidden(server_client):
    _, client, auth = server_client
    assert_hidden(client.post("/api/health-assessment", json=BODY, headers=auth), 500)


def test_diet_generation_error_is_hidden(server_client, monkeypatch):
    server, client, _ = server_client

    async def boom(*args, **kwargs):
        raise RuntimeError(SECRET_DETAIL)
    monkeypatch.setattr(server, "generate_diet_blueprint", boom)
    assert_hidden(client.post("/api/diet/recommend", json=BODY), 502)
