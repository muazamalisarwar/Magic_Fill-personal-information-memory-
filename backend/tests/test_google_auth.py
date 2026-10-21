"""
Automated Backend Tests for Google Authentication (Continue with Google)
Validates server-side token verification, PostgreSQL database persistence,
safe account linking, repeat login deduplication, and browser extension compatibility.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import User, PersonalInfo


@pytest.fixture
def mock_google_verifier():
    """Mock Google ID token verifier to simulate Google Identity Services responses."""
    with patch("app.services.auth_service.verify_google_id_token") as mock_verify:
        yield mock_verify


def test_auth_config_endpoint(client: TestClient):
    """Test retrieving public auth config containing Google Client ID."""
    res = client.get("/api/auth/config")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert "google_client_id" in json_data["data"]
    assert json_data["data"]["google_client_id"] is not None


def test_google_signup_new_user_persisted_in_db(client: TestClient, db_session: Session, mock_google_verifier):
    """
    Test 1: Register a new user through Continue with Google.
    Verifies that the backend returns successful authentication,
    and exactly one corresponding user record is persisted in PostgreSQL.
    """
    google_sub = "google-sub-alpha-12345"
    google_email = "alice.wonderland@example.com"
    google_name = "Alice Wonderland"
    google_pic = "https://lh3.googleusercontent.com/a/alice.jpg"

    mock_google_verifier.return_value = {
        "sub": google_sub,
        "email": google_email,
        "email_verified": True,
        "name": google_name,
        "picture": google_pic,
        "iss": "https://accounts.google.com"
    }

    # Execute Google authentication endpoint
    response = client.post("/api/auth/google", json={"credential": "mock-valid-google-id-token"})
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["is_new_user"] is True
    assert data["user"]["email"] == google_email
    assert data["user"]["full_name"] == google_name
    assert data["user"]["auth_provider"] == "google"
    assert data["user"]["avatar_url"] == google_pic
    user_id = data["user"]["id"]

    # Verify directly in the PostgreSQL database
    db_users = db_session.query(User).filter(User.google_id == google_sub).all()
    assert len(db_users) == 1
    db_user = db_users[0]
    assert db_user.id == user_id
    assert db_user.email == google_email
    assert db_user.auth_provider == "google"
    assert db_user.avatar_url == google_pic
    assert db_user.hashed_password is None  # Google passwords are never stored

    # Verify PersonalInfo record created and linked
    personal_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == user_id).first()
    assert personal_info is not None
    assert personal_info.full_name == google_name
    assert personal_info.email == google_email


def test_google_repeat_login_reuses_existing_user(client: TestClient, db_session: Session, mock_google_verifier):
    """
    Test 2: Repeated Google logins must reuse the existing user rather than create a new row.
    """
    google_sub = "google-sub-repeat-67890"
    google_email = "repeat.user@example.com"
    google_name = "Repeat User"

    mock_google_verifier.return_value = {
        "sub": google_sub,
        "email": google_email,
        "email_verified": True,
        "name": google_name,
        "picture": "https://lh3.googleusercontent.com/a/repeat.jpg",
        "iss": "https://accounts.google.com"
    }

    # 1st sign-in (creates user)
    res1 = client.post("/api/auth/google", json={"credential": "token-1"})
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    initial_user_id = data1["user"]["id"]
    assert data1["is_new_user"] is True

    # 2nd sign-in with same Google account
    res2 = client.post("/api/auth/google", json={"credential": "token-2"})
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert data2["is_new_user"] is False
    assert data2["user"]["id"] == initial_user_id  # Exact same user ID!

    # Verify in PostgreSQL database: Exactly ONE user exists with this google_id
    count = db_session.query(User).filter(User.google_id == google_sub).count()
    assert count == 1


def test_google_second_account_creates_separate_user(client: TestClient, db_session: Session, mock_google_verifier):
    """
    Test 3: A different Google account creates a separate user with distinct ID.
    """
    sub_1 = "google-sub-user-one"
    sub_2 = "google-sub-user-two"

    mock_google_verifier.return_value = {
        "sub": sub_1,
        "email": "user1@example.com",
        "email_verified": True,
        "name": "User One",
        "iss": "https://accounts.google.com"
    }
    res1 = client.post("/api/auth/google", json={"credential": "token-user-1"})
    assert res1.status_code == 200
    user1_id = res1.json()["data"]["user"]["id"]

    mock_google_verifier.return_value = {
        "sub": sub_2,
        "email": "user2@example.com",
        "email_verified": True,
        "name": "User Two",
        "iss": "https://accounts.google.com"
    }
    res2 = client.post("/api/auth/google", json={"credential": "token-user-2"})
    assert res2.status_code == 200
    user2_id = res2.json()["data"]["user"]["id"]

    assert user1_id != user2_id

    # Verify both records exist in DB
    u1 = db_session.query(User).filter(User.google_id == sub_1).first()
    u2 = db_session.query(User).filter(User.google_id == sub_2).first()
    assert u1 is not None and u2 is not None
    assert u1.id != u2.id


def test_google_safe_account_linking_with_local_user(client: TestClient, db_session: Session, mock_google_verifier):
    """
    Test 4: Safe account linking:
    When an account with matching email exists, link Google ID if email is verified.
    """
    shared_email = "charlie.brown@example.com"

    # Register local user with password
    reg_res = client.post("/api/auth/register", json={
        "email": shared_email,
        "password": "Password123!",
        "full_name": "Charlie Brown"
    })
    assert reg_res.status_code == 201
    local_user_id = reg_res.json()["data"]["user"]["id"]

    # Now sign in with Google using the same verified email
    google_sub = "google-sub-charlie-777"
    mock_google_verifier.return_value = {
        "sub": google_sub,
        "email": shared_email,
        "email_verified": True,
        "name": "Charlie Brown",
        "picture": "https://lh3.googleusercontent.com/charlie.png",
        "iss": "https://accounts.google.com"
    }

    google_res = client.post("/api/auth/google", json={"credential": "charlie-google-token"})
    assert google_res.status_code == 200
    google_data = google_res.json()["data"]
    assert google_data["is_new_user"] is False
    assert google_data["user"]["id"] == local_user_id

    # Verify in DB that existing account now has google_id linked
    db_user = db_session.query(User).filter(User.id == local_user_id).first()
    assert db_user.google_id == google_sub
    # User can still log in using regular password!
    login_res = client.post("/api/auth/login", json={
        "email": shared_email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200


def test_google_invalid_and_expired_tokens_rejected(client: TestClient):
    """
    Test 5: Invalid and malformed Google ID tokens are rejected.
    """
    # Empty token (rejected by schema validator with 422)
    res1 = client.post("/api/auth/google", json={"credential": ""})
    assert res1.status_code == 422

    # Completely bogus/tampered token
    res2 = client.post("/api/auth/google", json={"credential": "invalid.tampered.token"})
    assert res2.status_code in (400, 401)
    assert res2.json()["success"] is False


def test_google_user_extension_code_handoff(client: TestClient, mock_google_verifier):
    """
    Test 6: Verify website-to-extension authorization handoff for Google-authenticated user.
    """
    mock_google_verifier.return_value = {
        "sub": "google-sub-extension-test",
        "email": "ext.user@example.com",
        "email_verified": True,
        "name": "Extension User",
        "iss": "https://accounts.google.com"
    }
    # Authenticate via Google
    auth_res = client.post("/api/auth/google", json={"credential": "valid-token"})
    assert auth_res.status_code == 200
    token = auth_res.json()["data"]["access_token"]
    user_id = auth_res.json()["data"]["user"]["id"]

    # Generate single-use extension pairing code
    code_res = client.post(
        "/api/auth/extension/create-code",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert code_res.status_code == 200
    auth_code = code_res.json()["data"]["code"]
    assert auth_code.startswith("MF-")

    # Extension exchanges code
    exchange_res = client.post(
        "/api/auth/extension/exchange-code",
        json={"code": auth_code}
    )
    assert exchange_res.status_code == 200
    ext_data = exchange_res.json()["data"]
    assert "access_token" in ext_data
    assert ext_data["user"]["id"] == user_id
