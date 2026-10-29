import os
import sys

import bcrypt
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters")

from rate_limit import SlidingWindowLimiter  # noqa: E402


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


# ---------- SlidingWindowLimiter ----------

def test_blocks_after_max_events_and_reports_wait():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(3, 60, clock=clock)
    for _ in range(3):
        assert limiter.retry_after("k") == 0
        limiter.hit("k")
    assert limiter.retry_after("k") == 60
    clock.now += 45
    assert limiter.retry_after("k") == 15


def test_window_slides():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(2, 60, clock=clock)
    limiter.hit("k")
    clock.now += 30
    limiter.hit("k")
    clock.now += 31  # first hit has expired, second hasn't
    assert limiter.retry_after("k") == 0
    limiter.hit("k")
    assert limiter.retry_after("k") == 29


def test_keys_are_independent_and_reset_clears():
    limiter = SlidingWindowLimiter(1, 60, clock=FakeClock())
    limiter.hit("a")
    assert limiter.retry_after("a") > 0
    assert limiter.retry_after("b") == 0
    limiter.reset("a")
    assert limiter.retry_after("a") == 0


def test_undo_removes_latest_event():
    limiter = SlidingWindowLimiter(2, 60, clock=FakeClock())
    limiter.hit("k")
    limiter.hit("k")
    limiter.undo("k")
    assert limiter.retry_after("k") == 0


def test_memory_is_bounded():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(5, 60, max_keys=10, clock=clock)
    for i in range(100):
        limiter.hit(f"key{i}")
    assert len(limiter._events) <= 10
    assert all(len(q) <= 5 for q in limiter._events.values())


# ---------- auth endpoints ----------

PASSWORD = "right-password"


class FakeDAL:
    def __init__(self):
        hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
        self.users = {"user@example.com": {"id": 1, "name": "U", "email": "user@example.com", "password": hashed}}

    async def get_user_by_email(self, email):
        return self.users.get(email)

    async def create_user(self, name, email, hashed_password):
        self.users[email] = {"id": len(self.users) + 1, "name": name, "email": email, "password": hashed_password}
        return self.users[email]["id"]

    async def create_refresh_token(self, *args):
        pass


@pytest.fixture
def client(monkeypatch):
    import server
    from fastapi.testclient import TestClient

    # Fresh counters per test, with small limits so the tests stay fast
    monkeypatch.setattr(server, "login_attempts_by_email", SlidingWindowLimiter(3, 900))
    monkeypatch.setattr(server, "login_attempts_by_ip", SlidingWindowLimiter(6, 900))
    monkeypatch.setattr(server, "registrations_by_ip", SlidingWindowLimiter(2, 3600))
    server.app.state.dal = FakeDAL()
    return TestClient(server.app)


def login(client, email="user@example.com", password="wrong"):
    return client.post("/api/login", json={"email": email, "password": password})


def test_login_locks_email_after_repeated_failures(client):
    for _ in range(3):
        assert login(client).status_code == 401
    r = login(client, password=PASSWORD)  # even the right password is refused while locked
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0
    assert "Too many attempts" in r.json()["detail"]


def test_email_limit_ignores_case(client):
    for email in ("user@example.com", "USER@example.com", "User@Example.com"):
        login(client, email=email)
    assert login(client).status_code == 429


def test_successful_login_resets_email_counter(client):
    login(client)
    login(client)
    assert login(client, password=PASSWORD).status_code == 200
    assert login(client).status_code == 401  # counter restarted, so not yet locked


def test_ip_limit_spans_emails(client):
    for i in range(6):
        login(client, email=f"guess{i}@example.com")
    assert login(client, email="another@example.com").status_code == 429


def test_oauth_token_endpoint_shares_limits(client):
    for _ in range(3):
        login(client)
    r = client.post("/api/token", data={"username": "user@example.com", "password": PASSWORD})
    assert r.status_code == 429


def test_register_limited_per_ip(client):
    for i in range(2):
        r = client.post("/api/register", json={"name": "N", "email": f"new{i}@example.com", "password": "pw123456"})
        assert r.status_code == 200
    r = client.post("/api/register", json={"name": "N", "email": "new9@example.com", "password": "pw123456"})
    assert r.status_code == 429
