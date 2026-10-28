"""Auth contract tests. Owner: Asra (scaffold), reviewed by Sana."""

from __future__ import annotations

VALID = {
    "email": "New.User@Example.com",
    "password": "Demo1234!",
    "full_name": "New User",
}


def test_register_returns_token_and_user(client):
    res = client.post("/api/v1/auth/register", json=VALID)
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "new.user@example.com"  # normalised
    assert "password_hash" not in data["user"]


def test_register_duplicate_email(client):
    assert client.post("/api/v1/auth/register", json=VALID).status_code == 201
    res = client.post("/api/v1/auth/register", json=VALID)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_register_weak_password(client):
    res = client.post(
        "/api/v1/auth/register",
        json={**VALID, "password": "onlyletters"},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_and_me(client):
    client.post("/api/v1/auth/register", json=VALID)
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "new.user@example.com", "password": "Demo1234!"},
    )
    assert res.status_code == 200, res.text
    token = res.json()["data"]["access_token"]

    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["data"]["full_name"] == "New User"


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json=VALID)
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "new.user@example.com", "password": "Wrong1234"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"
    # Never reveal which half was wrong
    assert "password" in res.json()["error"]["message"].lower()


def test_me_without_token(client):
    res = client.get("/api/v1/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_with_garbage_token(client):
    res = client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-token"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_unknown_field_is_rejected(client):
    res = client.post("/api/v1/auth/register", json={**VALID, "fullName": "wrong"})
    assert res.status_code == 422
    assert "fullName" in res.json()["error"]["details"]["fields"]
