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


def test_delete_personal_info(client):
    """Test deleting personal info removes the record and allows re-creation."""
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "Temporary Profile", "city": "Lahore"}
    )

    # Delete personal info
    del_res = client.delete(f"/api/users/{user_id}/personal-info")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify subsequent GET returns 404
    get_res = client.get(f"/api/users/{user_id}/personal-info")
    assert get_res.status_code == 404
    assert get_res.json()["error_code"] == "PERSONAL_INFO_NOT_FOUND"

    # Verify a new profile can be created now
    create_res = client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "New Recreated Profile"}
    )
    assert create_res.status_code == 201


def test_delete_user_cascades(client):
    """Test deleting user cascades deletion to personal info and experiences."""
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "Cascade User"}
    )
    client.post(
        f"/api/users/{user_id}/experiences",
        json={"company": "Test Corp", "job_title": "Dev", "start_date": "2024-01-01"}
    )

    # Delete user
    del_res = client.delete(f"/api/users/{user_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify user no longer exists
    assert client.get(f"/api/users/{user_id}").status_code == 404
    assert client.get(f"/api/users/{user_id}/personal-info").status_code == 404
    assert client.get(f"/api/users/{user_id}/experiences").status_code == 404


def test_update_personal_info_null_full_name_fails(client):
    """Test updating personal info with null full_name fails with 422 validation error."""
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "Valid Name"}
    )

    update_res = client.put(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": None}
    )
    assert update_res.status_code == 422
    assert update_res.json()["error_code"] == "VALIDATION_ERROR"


def test_get_user_profile(client):
    """Test retrieving full aggregated profile with personal info and experiences."""
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "Full Profile User", "university": "FAST NUCES"}
    )
    client.post(
        f"/api/users/{user_id}/experiences",
        json={"company": "Company A", "job_title": "Engineer", "start_date": "2024-01-01"}
    )

    profile_res = client.get(f"/api/users/{user_id}/profile")
    assert profile_res.status_code == 200
    data = profile_res.json()["data"]
    assert data["user"]["id"] == user_id
    assert data["personal_info"]["full_name"] == "Full Profile User"
    assert len(data["experiences"]) == 1
    assert data["experiences"][0]["company"] == "Company A"


def test_create_and_get_personal_info_with_gender_and_photos(client):
    """Test creating and updating personal information with gender and base64 photos."""
    user_id = client.post("/api/users", json={}).json()["data"]["id"]

    photo_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    cnic_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    payload = {
        "full_name": "Ayesha Khan",
        "gender": "Female",
        "profile_photo": photo_uri,
        "cnic_photo": cnic_uri
    }
    create_res = client.post(f"/api/users/{user_id}/personal-info", json=payload)
    assert create_res.status_code == 201
    created_info = create_res.json()["data"]
    assert created_info["gender"] == "Female"
    assert created_info["profile_photo"] == photo_uri
    assert created_info["cnic_photo"] == cnic_uri

    # Verify update
    update_res = client.put(
        f"/api/users/{user_id}/personal-info",
        json={"gender": "Other"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["gender"] == "Other"
    assert update_res.json()["data"]["profile_photo"] == photo_uri


