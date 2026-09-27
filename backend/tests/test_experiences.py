def test_create_and_retrieve_multiple_experiences(client):
    """Test creating multiple experiences for a user and retrieving the list."""
    # 1. Create a user
    user_id = client.post("/api/users", json={}).json()["data"]["id"]

    # 2. Add first experience (Software Development Intern)
    exp1_payload = {
        "company": "Alpha Tech",
        "job_title": "Software Development Intern",
        "start_date": "2024-06-01",
        "end_date": "2024-09-01",
        "description": "Developed backend APIs using FastAPI and PostgreSQL",
        "skills": "FastAPI, PostgreSQL, Git"
    }
    exp1_res = client.post(f"/api/users/{user_id}/experiences", json=exp1_payload)
    assert exp1_res.status_code == 201
    exp1_data = exp1_res.json()
    assert exp1_data["success"] is True
    assert exp1_data["data"]["company"] == "Alpha Tech"
    exp1_id = exp1_data["data"]["id"]

    # 3. Add second experience (Active AI/ML Intern with end_date=None)
    exp2_payload = {
        "company": "Beta AI Labs",
        "job_title": "AI/ML Intern",
        "start_date": "2025-01-15",
        "end_date": None,
        "description": "Researching RAG and vector databases",
        "skills": "Python, PyTorch, Embeddings"
    }
    exp2_res = client.post(f"/api/users/{user_id}/experiences", json=exp2_payload)
    assert exp2_res.status_code == 201
    exp2_data = exp2_res.json()
    assert exp2_data["success"] is True
    assert exp2_data["data"]["end_date"] is None
    exp2_id = exp2_data["data"]["id"]

    # 4. Add third experience (CMS Developer)
    exp3_payload = {
        "company": "Gamma Solutions",
        "job_title": "CMS Developer",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "description": "Managed CMS platforms",
        "skills": "WordPress, PHP, MySQL"
    }
    client.post(f"/api/users/{user_id}/experiences", json=exp3_payload)

    # 5. Retrieve all experiences for user
    get_all_res = client.get(f"/api/users/{user_id}/experiences")
    assert get_all_res.status_code == 200
    all_exps = get_all_res.json()
    assert all_exps["success"] is True
    assert len(all_exps["data"]) == 3
    # Check that the newest experience comes first (ordered by start_date desc)
    assert all_exps["data"][0]["company"] == "Beta AI Labs"

    # 6. Retrieve individual experience
    get_one_res = client.get(f"/api/experiences/{exp1_id}")
    assert get_one_res.status_code == 200
    one_data = get_one_res.json()
    assert one_data["success"] is True
    assert one_data["data"]["id"] == exp1_id
    assert one_data["data"]["company"] == "Alpha Tech"


def test_update_experience(client):
    """Test updating an existing experience by experience ID."""
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    exp_payload = {
        "company": "Old Corp",
        "job_title": "Junior Engineer",
        "start_date": "2024-01-01",
        "end_date": "2024-06-01",
        "description": "Initial description",
        "skills": "Python"
    }
    exp_res = client.post(f"/api/users/{user_id}/experiences", json=exp_payload)
    exp_id = exp_res.json()["data"]["id"]

    # Update title and skills
    update_res = client.put(
        f"/api/experiences/{exp_id}",
        json={
            "job_title": "Senior Engineer",
            "skills": "Python, Docker, Kubernetes"
        }
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["success"] is True
    assert updated_data["data"]["job_title"] == "Senior Engineer"
    assert updated_data["data"]["company"] == "Old Corp"  # preserved
    assert updated_data["data"]["skills"] == "Python, Docker, Kubernetes"


def test_invalid_date_range_validation(client):
    """Test that end_date earlier than start_date is rejected with 422."""
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    invalid_payload = {
        "company": "Time Travelers Inc.",
        "job_title": "Paradox Specialist",
        "start_date": "2025-05-01",
        "end_date": "2024-05-01"  # end before start
    }
    res = client.post(f"/api/users/{user_id}/experiences", json=invalid_payload)
    assert res.status_code == 422
    body = res.json()
    assert body["success"] is False
    assert body["error_code"] == "VALIDATION_ERROR"


def test_experience_non_existent_user(client):
    """Test creating or retrieving experiences for a non-existent user returns 404."""
    exp_payload = {
        "company": "Ghost Corp",
        "job_title": "Ghost",
        "start_date": "2024-01-01"
    }
    # Create for non-existent user
    res = client.post("/api/users/99999/experiences", json=exp_payload)
    assert res.status_code == 404
    assert res.json()["error_code"] == "USER_NOT_FOUND"

    # Get for non-existent user
    res_get = client.get("/api/users/99999/experiences")
    assert res_get.status_code == 404
    assert res_get.json()["error_code"] == "USER_NOT_FOUND"


def test_non_existent_experience(client):
    """Test retrieving and updating a non-existent experience ID returns 404."""
    # Get non-existent
    res = client.get("/api/experiences/99999")
    assert res.status_code == 404
    assert res.json()["error_code"] == "EXPERIENCE_NOT_FOUND"

    # Update non-existent
    update_res = client.put("/api/experiences/99999", json={"company": "New Corp"})
    assert update_res.status_code == 404
    assert update_res.json()["error_code"] == "EXPERIENCE_NOT_FOUND"
