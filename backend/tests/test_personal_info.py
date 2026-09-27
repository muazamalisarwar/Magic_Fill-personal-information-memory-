def test_create_and_get_user(client):
    """Test user creation and retrieval."""
    # 1. Create user
    create_res = client.post("/api/users", json={})
    assert create_res.status_code == 201
    created_user = create_res.json()
    assert created_user["success"] is True
    assert created_user["message"] == "User created successfully"
    user_id = created_user["data"]["id"]
    assert user_id > 0

    # 2. Retrieve user
    get_res = client.get(f"/api/users/{user_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["success"] is True
    assert retrieved["data"]["id"] == user_id


def test_get_non_existent_user(client):
    """Test retrieving a non-existent user returns 404 with standard error body."""
    response = client.get("/api/users/99999")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "USER_NOT_FOUND"


def test_create_and_get_personal_info(client):
    """Test creating and retrieving personal information for a user."""
    # Create user
    user_res = client.post("/api/users", json={})
    user_id = user_res.json()["data"]["id"]

    # Create personal info
    payload = {
        "full_name": "Muazam Ali",
        "father_name": "Muhammad Ali",
        "date_of_birth": "2002-05-15",
        "cnic": "35202-1234567-1",
        "phone": "+92 300 1234567",
        "email": "muazam@example.com",
        "address": "Street 10, Sector F-8",
        "city": "Islamabad",
        "postal_code": "44000",
        "country": "Pakistan",
        "university": "FAST NUCES",
        "degree": "BS Computer Science",
        "department": "Computer Science",
        "semester": "8th",
        "registration_number": "21F-1234"
    }
    create_res = client.post(f"/api/users/{user_id}/personal-info", json=payload)
    assert create_res.status_code == 201
    created_info = create_res.json()
    assert created_info["success"] is True
    assert created_info["data"]["full_name"] == "Muazam Ali"
    assert created_info["data"]["user_id"] == user_id
    assert created_info["data"]["email"] == "muazam@example.com"

    # Get personal info
    get_res = client.get(f"/api/users/{user_id}/personal-info")
    assert get_res.status_code == 200
    retrieved_info = get_res.json()
    assert retrieved_info["success"] is True
    assert retrieved_info["data"]["full_name"] == "Muazam Ali"
    assert retrieved_info["data"]["university"] == "FAST NUCES"


def test_update_personal_info(client):
    """Test updating existing personal information (partial update)."""
    # Create user and info
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "Original Name", "city": "Lahore"}
    )

    # Update personal info
    update_res = client.put(
        f"/api/users/{user_id}/personal-info",
        json={"city": "Islamabad", "degree": "MS Software Engineering"}
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["success"] is True
    assert updated["data"]["full_name"] == "Original Name"  # preserved
    assert updated["data"]["city"] == "Islamabad"          # updated
    assert updated["data"]["degree"] == "MS Software Engineering"


def test_duplicate_personal_info_fails(client):
    """Test that creating personal info twice for the same user returns 400."""
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "First Entry"}
    )

    duplicate_res = client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "Duplicate Entry"}
    )
    assert duplicate_res.status_code == 400
    body = duplicate_res.json()
    assert body["success"] is False
    assert body["error_code"] == "PERSONAL_INFO_ALREADY_EXISTS"


def test_personal_info_non_existent_user(client):
    """Test operations on personal info for a non-existent user return 404."""
    # Create for non-existent user
    res = client.post(
        "/api/users/99999/personal-info",
        json={"full_name": "Ghost User"}
    )
    assert res.status_code == 404
    assert res.json()["error_code"] == "USER_NOT_FOUND"

    # Get for non-existent user
    res_get = client.get("/api/users/99999/personal-info")
    assert res_get.status_code == 404
    assert res_get.json()["error_code"] == "USER_NOT_FOUND"


def test_invalid_email_validation(client):
    """Test that invalid email format triggers 422 validation error."""
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    res = client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "Test User", "email": "not-an-email"}
    )
    assert res.status_code == 422
    body = res.json()
    assert body["success"] is False
    assert body["error_code"] == "VALIDATION_ERROR"
