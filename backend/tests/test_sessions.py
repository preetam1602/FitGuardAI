import os
import sys
from datetime import datetime

import bcrypt
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters")

from rate_limit import SlidingWindowLimiter  # noqa: E402

PASSWORD = "right-password"
BASE_URL = "https://testserver"  # the refresh cookie is Secure, so the test client must use https


class FakeDAL:
    """In-memory stand-in that mirrors the refresh-token semantics of FitGuardDAL."""

    def __init__(self):
        hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
        self.users = {1: {"id": 1, "name": "U", "email": "user@example.com", "password": hashed}}
        self.tokens = {}  # hash -> {user_id, family_id, expires_at, revoked}

    async def get_user_by_email(self, email):
        return next((u for u in self.users.values() if u["email"] == email), None)

    async def get_user_by_id(self, user_id):
        return self.users.get(user_id)

    async def create_user(self, name, email, hashed_password):
        user_id = len(self.users) + 1
        self.users[user_id] = {"id": user_id, "name": name, "email": email, "password": hashed_password}
        return user_id

    async def create_refresh_token(self, user_id, token_hash, family_id, expires_at):
        self.tokens[token_hash] = {"user_id": user_id, "family_id": family_id, "expires_at": expires_at, "revoked": False}

    async def rotate_refresh_token(self, old_hash, new_hash, expires_at):
        row = self.tokens.get(old_hash)
        if row is None:
            return {"status": "invalid"}
        if row["revoked"]:
            for t in self.tokens.values():
                if t["family_id"] == row["family_id"]:
                    t["revoked"] = True
            return {"status": "reused", "user_id": row["user_id"]}
        if row["expires_at"] <= datetime.utcnow():
            return {"status": "expired"}
        row["revoked"] = True
        await self.create_refresh_token(row["user_id"], new_hash, row["family_id"], expires_at)
        return {"status": "ok", "user_id": row["user_id"]}

    async def revoke_refresh_token_family(self, token_hash):
        row = self.tokens.get(token_hash)
        if row:
            for t in self.tokens.values():
                if t["family_id"] == row["family_id"]:
                    t["revoked"] = True


@pytest.fixture
def ctx(monkeypatch):
    import server
    from fastapi.testclient import TestClient

    monkeypatch.setattr(server, "login_attempts_by_email", SlidingWindowLimiter(100, 900))
    monkeypatch.setattr(server, "login_attempts_by_ip", SlidingWindowLimiter(100, 900))
    monkeypatch.setattr(server, "registrations_by_ip", SlidingWindowLimiter(100, 3600))
    dal = FakeDAL()
    server.app.state.dal = dal
    return server, TestClient(server.app, base_url=BASE_URL), dal


def login(client):
    return client.post("/api/login", json={"email": "user@example.com", "password": PASSWORD})


def refresh_cookie(response):
    return response.cookies.get("fitguard_refresh")


def test_login_sets_hardened_refresh_cookie(ctx):
    _, client, _ = ctx
    r = login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["user"]["email"] == "user@example.com"
    header = r.headers["set-cookie"].lower()
    for attribute in ("httponly", "secure", "samesite=strict", "path=/api/auth"):
        assert attribute in header
    assert refresh_cookie(r) not in r.text  # the refresh token never appears in the JSON body


def test_refresh_rotates_cookie_and_returns_working_access_token(ctx):
    _, client, _ = ctx
    first = refresh_cookie(login(client))
    r = client.post("/api/auth/refresh")
    assert r.status_code == 200
    assert refresh_cookie(r) and refresh_cookie(r) != first
    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.json()["email"] == "user@example.com"


def test_reusing_an_old_refresh_token_revokes_the_session(ctx):
    _, client, _ = ctx
    stolen = refresh_cookie(login(client))
    assert client.post("/api/auth/refresh").status_code == 200   # legitimate user rotates
    client.cookies.clear()
    r = client.post("/api/auth/refresh", cookies={"fitguard_refresh": stolen})  # attacker replays
    assert r.status_code == 401
    assert 'fitguard_refresh=""' in r.headers["set-cookie"]  # cookie cleared
    # ...and the legitimate user's current token is now dead too
    client.cookies.clear()
    assert client.post("/api/auth/refresh").status_code == 401


def test_refresh_without_cookie_is_rejected(ctx):
    _, client, _ = ctx
    assert client.post("/api/auth/refresh").status_code == 401


def test_logout_revokes_refresh_token(ctx):
    _, client, _ = ctx
    token = refresh_cookie(login(client))
    assert client.post("/api/auth/logout").status_code == 204
    r = client.post("/api/auth/refresh", cookies={"fitguard_refresh": token})
    assert r.status_code == 401


def test_register_starts_a_session(ctx):
    _, client, _ = ctx
    r = client.post("/api/register", json={"name": " New ", "email": "new@example.com", "password": "pw123456"})
    assert r.status_code == 200
    assert r.json()["user"]["name"] == "New"
    assert refresh_cookie(r)


def test_old_bearer_refresh_endpoint_is_gone(ctx):
    _, client, _ = ctx
    token = login(client).json()["access_token"]
    r = client.post("/api/token/refresh", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code in (404, 405)


@pytest.mark.parametrize("password", ["short", "x" * 73, "é" * 37])  # 37 × 2 bytes = 74 bytes
def test_register_rejects_out_of_range_passwords(ctx, password):
    _, client, _ = ctx
    r = client.post("/api/register", json={"name": "N", "email": "p@example.com", "password": password})
    assert r.status_code == 422


def test_overlong_password_login_is_a_clean_401(ctx):
    _, client, _ = ctx
    r = client.post("/api/login", json={"email": "user@example.com", "password": "x" * 100})
    assert r.status_code == 401


def test_unknown_email_still_runs_a_password_check(ctx, monkeypatch):
    server, client, _ = ctx
    checked = []
    real_verify = server.verify_password

    async def spy(password, hashed):
        checked.append(hashed)
        return await real_verify(password, hashed)
    monkeypatch.setattr(server, "verify_password", spy)
    r = client.post("/api/login", json={"email": "nobody@example.com", "password": "whatever1"})
    assert r.status_code == 401
    assert checked == [server._DUMMY_PASSWORD_HASH]


# ---------- diet generation limits ----------

BODY = dict(age=50, gender="male", height=175, weight=80, bloodPressure="130/85", heartRate=72,
            physicalActivity="moderate", sleepHours=7, smokingHabit="no")


def test_anonymous_diet_endpoint_is_limited_per_ip(ctx, monkeypatch):
    server, client, _ = ctx
    monkeypatch.setattr(server, "anonymous_diet_generations_by_ip", SlidingWindowLimiter(2, 3600))

    async def fake_diet(*args, **kwargs):
        return {"diet_type": "DASH"}
    monkeypatch.setattr(server, "generate_diet_blueprint", fake_diet)
    assert [client.post("/api/diet/recommend", json=BODY).status_code for _ in range(3)] == [200, 200, 429]


def test_diet_stream_is_limited_per_user(ctx, monkeypatch):
    server, client, dal = ctx
    from dal import HealthRecord
    monkeypatch.setattr(server, "diet_generations_by_user", SlidingWindowLimiter(1, 3600))

    async def get_health_record(record_id):
        return HealthRecord(id=record_id, user_id=1, age=50, gender="male", height_cm=175, weight_kg=80, bmi=26.1,
                            blood_pressure="130/85", heart_rate=72, physical_activity="moderate", sleep_hours=7,
                            smoking_habit=False, created_at=datetime.utcnow())

    async def save_diet_blueprint(**kwargs):
        pass

    async def fake_diet(*args, **kwargs):
        return {"diet_type": "DASH"}
    dal.get_health_record, dal.save_diet_blueprint = get_health_record, save_diet_blueprint
    monkeypatch.setattr(server, "generate_diet_blueprint", fake_diet)

    auth = {"Authorization": f"Bearer {login(client).json()['access_token']}"}
    assert client.post("/api/records/5/diet/stream", headers=auth).status_code == 200
    r = client.post("/api/records/5/diet/stream", headers=auth)
    assert r.status_code == 429
    assert "diet plans" in r.json()["detail"]
