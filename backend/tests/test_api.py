"""End-to-end API tests. Run from backend/:   python -m pytest tests/test_api.py -v

Uses a throwaway SQLite database by default, so it never touches your real PostgreSQL data.
To also test against PostgreSQL, create a SEPARATE empty database (e.g. payguard_test) and set
PAYGUARD_TEST_DATABASE_URL to it before running. Never point this at your real database: the
tests create users and predictions.
Needs models/inference_bundle.pkl (the real model) to exist.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

TX = {
    "sender_vpa": "user12345678@okaxis",
    "receiver_vpa": "user87654321@ybl",
    "timestamp": "2026-01-05T03:15:00",
    "transaction_mode": "TRANSFER",
    "amount": 181000,
    "sender_balance_before": 181000,
    "sender_balance_after": 0,
    "receiver_balance_before": 0,
    "receiver_balance_after": 0,
}


@pytest.fixture(scope="module")
def client():
    tmp = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = os.getenv("PAYGUARD_TEST_DATABASE_URL") or (
        f"sqlite:///{Path(tmp, 'test.db').as_posix()}"
    )  # always a test DB, never the DATABASE_URL from .env
    os.environ["PAYGUARD_SECRET_KEY"] = "test-secret-key-not-for-production-use-0123456789"
    os.environ["ALLOW_REGISTRATION"] = "true"
    from app.main import app  # imported only after the env vars are set

    with TestClient(app) as c:
        yield c


def register_and_login(client, username, password="correct-horse-battery"):
    client.post("/auth/register", json={"username": username, "password": password})
    r = client.post("/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health_is_open(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_predict_requires_login(client):
    assert client.post("/predict", json=TX).status_code == 401
    assert client.get("/predictions").status_code == 401


def test_register_rules(client):
    ok = client.post("/auth/register", json={"username": "Alice", "password": "correct-horse-battery"})
    assert ok.status_code == 201 and ok.json()["username"] == "alice"          # lower-cased
    dup = client.post("/auth/register", json={"username": "ALICE", "password": "another-password-1"})
    assert dup.status_code == 409
    short = client.post("/auth/register", json={"username": "bob", "password": "short"})
    assert short.status_code == 422
    assert "hashed_password" not in ok.json()


def test_login_rules(client):
    client.post("/auth/register", json={"username": "carol", "password": "correct-horse-battery"})
    wrong = client.post("/auth/login", data={"username": "carol", "password": "wrong-password-1"})
    ghost = client.post("/auth/login", data={"username": "nobody", "password": "wrong-password-1"})
    assert wrong.status_code == ghost.status_code == 401
    assert wrong.json() == ghost.json()                       # no user enumeration
    headers = register_and_login(client, "carol")
    assert client.get("/auth/me", headers=headers).json()["username"] == "carol"


def test_bad_tokens_rejected(client):
    assert client.get("/auth/me", headers={"Authorization": "Bearer not.a.token"}).status_code == 401
    headers = register_and_login(client, "dave")
    tampered = {"Authorization": headers["Authorization"][:-3] + "abc"}
    assert client.get("/auth/me", headers=tampered).status_code == 401


def test_predict_saves_history_and_isolates_users(client):
    erin = register_and_login(client, "erin")
    frank = register_and_login(client, "frank")

    r = client.post("/predict", json=TX, headers=erin)
    assert r.status_code == 200, r.text
    body = r.json()
    assert 0.0 <= body["risk_score"] <= 1.0
    assert body["label"] in ("fraud", "not_fraud")
    assert len(body["top_contributors"]) == 5
    pid = body["prediction_id"]

    hist = client.get("/predictions", headers=erin).json()
    assert [h["id"] for h in hist] == [pid]
    assert hist[0]["created_at"].endswith("+00:00") or hist[0]["created_at"].endswith("Z")
    assert client.get(f"/predictions/{pid}", headers=erin).status_code == 200

    # another analyst must not see it
    assert client.get("/predictions", headers=frank).json() == []
    assert client.get(f"/predictions/{pid}", headers=frank).status_code == 404


def test_history_filter_and_paging(client):
    gina = register_and_login(client, "gina")
    for _ in range(3):
        assert client.post("/predict", json=TX, headers=gina).status_code == 200
    assert len(client.get("/predictions?limit=2", headers=gina).json()) == 2
    ids = [h["id"] for h in client.get("/predictions", headers=gina).json()]
    assert ids == sorted(ids, reverse=True)                   # newest first
    assert client.get("/predictions?limit=0", headers=gina).status_code == 422


def test_input_validation(client):
    headers = register_and_login(client, "hank")
    assert client.post("/predict", json={**TX, "amount": -5}, headers=headers).status_code == 422
    assert client.post("/predict", json={**TX, "transaction_mode": "WIRE"}, headers=headers).status_code == 422
