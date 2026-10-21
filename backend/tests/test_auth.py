import pytest
from fastapi.testclient import TestClient

def test_register_new_user(client: TestClient):
    """Test registering a brand new user via website signup."""
    payload = {
        "email": "sarah.connor@example.com",
        "password": "Password123!",
        "full_name": "Sarah Connor"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["is_new_user"] is True
    assert data["user"]["email"] == "sarah.connor@example.com"
    assert data["user"]["full_name"] == "Sarah Connor"


def test_duplicate_email_registration_rejected(client: TestClient):
    """Test that registering an email that already exists is strictly rejected."""
    payload = {
        "email": "duplicate.test@example.com",
        "password": "Password123!",
        "full_name": "Original User"
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt second registration with same email
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    json_data = res2.json()
    assert json_data["success"] is False
    assert json_data["error_code"] == "DUPLICATE_EMAIL"


def test_login_success_and_failure(client: TestClient):
    """Test user login with valid credentials and rejection of invalid credentials."""
    reg_payload = {
        "email": "login.test@example.com",
        "password": "CorrectPassword123",
        "full_name": "Login Tester"
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    assert res_reg.status_code == 201

    # Login with wrong password
    bad_login = {
        "email": "login.test@example.com",
        "password": "WrongPassword!"
    }
    res_bad = client.post("/api/auth/login", json=bad_login)
    assert res_bad.status_code == 401
    assert res_bad.json()["error_code"] == "INVALID_CREDENTIALS"

    # Login with correct password
    good_login = {
        "email": "login.test@example.com",
        "password": "CorrectPassword123"
    }
    res_good = client.post("/api/auth/login", json=good_login)
    assert res_good.status_code == 200
    data = res_good.json()["data"]
    assert "access_token" in data
    assert data["user"]["email"] == "login.test@example.com"


def test_auth_me_endpoint(client: TestClient):
    """Test retrieving authenticated user identity via /api/auth/me."""
    reg_payload = {
        "email": "me.test@example.com",
        "password": "Password123!",
        "full_name": "Me Tester"
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    token = res_reg.json()["data"]["access_token"]

    # Request without token
    res_unauth = client.get("/api/auth/me")
    assert res_unauth.status_code == 401

    # Request with valid Bearer token
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["data"]["email"] == "me.test@example.com"
    assert res_me.json()["data"]["full_name"] == "Me Tester"


def test_extension_auth_code_handoff_and_anti_replay(client: TestClient):
    """
    Test secure website-to-extension authorization flow:
    1. Authenticated website session requests single-use code
    2. Extension exchanges code for an extension session token
    3. Reusing the same code is rejected (anti-replay)
    """
    reg_payload = {
        "email": "ext.user@example.com",
        "password": "Password123!",
        "full_name": "Extension User"
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    token = res_reg.json()["data"]["access_token"]
    user_id = res_reg.json()["data"]["user"]["id"]

    # Step 1: Website creates extension auth code
    res_code = client.post("/api/auth/extension/create-code", headers={"Authorization": f"Bearer {token}"})
    assert res_code.status_code == 200
    code = res_code.json()["data"]["code"]
    assert code.startswith("MF-")
    assert len(code) >= 10

    # Step 2: Extension exchanges code for token
    res_exchange = client.post(
        "/api/auth/extension/exchange-code",
        json={"code": code, "client_id": "chrome_extension"}
    )
    assert res_exchange.status_code == 200
    ext_data = res_exchange.json()["data"]
    assert "access_token" in ext_data
    assert ext_data["user"]["id"] == user_id

    # Step 3: Anti-replay protection — Reusing the same code must fail
    res_replay = client.post(
        "/api/auth/extension/exchange-code",
        json={"code": code, "client_id": "chrome_extension"}
    )
    assert res_replay.status_code == 400
    assert res_replay.json()["error_code"] == "INVALID_AUTH_CODE"


def test_user_data_isolation(client: TestClient):
    """Test that User A cannot access or modify User B's personal information."""
    # User A
    user_a = client.post("/api/auth/register", json={"email": "usera@example.com", "password": "Password123!", "full_name": "User A"}).json()["data"]
    token_a = user_a["access_token"]
    id_a = user_a["user"]["id"]

    # User B
    user_b = client.post("/api/auth/register", json={"email": "userb@example.com", "password": "Password123!", "full_name": "User B"}).json()["data"]
    token_b = user_b["access_token"]
    id_b = user_b["user"]["id"]

    # User A accesses User A's info -> Allowed
    res_own = client.get(f"/api/users/{id_a}/personal-info", headers={"Authorization": f"Bearer {token_a}"})
    assert res_own.status_code == 200

    # User A tries to access User B's personal info -> 403 Forbidden
    res_other = client.get(f"/api/users/{id_b}/personal-info", headers={"Authorization": f"Bearer {token_a}"})
    assert res_other.status_code == 403
    assert res_other.json()["error_code"] == "FORBIDDEN"


def test_frontend_auth_routes_serving(client: TestClient):
    """Test that dedicated website auth routes serve the frontend workstation."""
    for path in ["/login", "/register", "/onboarding"]:
        res = client.get(path)
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert "Magic Fill" in res.text


def test_invalid_token_rejected(client: TestClient):
    """Test that forged or malformed tokens are rejected with 401."""
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer totally.invalid.token"})
    assert res.status_code == 401
    assert res.json()["error_code"] == "INVALID_TOKEN"


def test_nonexistent_extension_code_rejected(client: TestClient):
    """Test that a fabricated or nonexistent authorization code cannot be exchanged."""
    res = client.post(
        "/api/auth/extension/exchange-code",
        json={"code": "MF-NONEXISTENT-CODE", "client_id": "test"}
    )
    assert res.status_code == 400
    assert res.json()["error_code"] == "INVALID_AUTH_CODE"

