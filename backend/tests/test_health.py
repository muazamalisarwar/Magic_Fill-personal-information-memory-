def test_health_check(client):
    """Test that the /health endpoint responds with 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "healthy"
    assert data["message"] == "Backend is running"


def test_docs_available(client):
    """Test that OpenAPI Swagger docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json_available(client):
    """Test that openapi.json is accessible and contains required API metadata."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Personal Information Memory API"
    assert schema["info"]["version"] == "1.0.0"
