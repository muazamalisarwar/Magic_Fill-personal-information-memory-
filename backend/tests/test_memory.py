import pytest
from unittest.mock import patch, AsyncMock
import io


@pytest.mark.anyio
async def test_extract_and_save_raw_text(client):
    """Test extracting personal memory from raw text and saving to database."""
    mock_extracted = {
        "personal_info": {
            "full_name": "Muazam Ali",
            "email": "muazam@example.com",
            "phone": "+92 300 1234567",
            "university": "University of Education, Lahore",
            "degree": "BS Information Technology"
        },
        "experiences": [
            {
                "company": "Apex Software Solutions",
                "job_title": "Full Stack Engineer",
                "start_date": "2024-01-01",
                "end_date": None,
                "skills": "Python, React"
            }
        ]
    }

    with patch("app.services.extraction_service.query_groq_llm", new=AsyncMock(return_value=mock_extracted)):
        res = client.post(
            "/api/memory/extract-raw",
            json={
                "raw_text": "My name is Muazam Ali from Lahore, graduated from University of Education, Lahore...",
                "user_id": 1,
                "auto_save": True
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["saved"] is True
        assert data["data"]["extracted"]["personal_info"]["full_name"] == "Muazam Ali"
        assert data["data"]["profile"]["personal_info"]["university"] == "University of Education, Lahore"
        assert len(data["data"]["profile"]["experiences"]) == 1

    # Verify persistent memory can be retrieved via /api/memory/current
    curr_res = client.get("/api/memory/current?user_id=1")
    assert curr_res.status_code == 200
    curr_data = curr_res.json()["data"]
    assert curr_data["personal_info"]["full_name"] == "Muazam Ali"
    assert curr_data["personal_info"]["university"] == "University of Education, Lahore"


@pytest.mark.anyio
async def test_upload_text_document(client):
    """Test uploading a text document for memory extraction."""
    mock_extracted = {
        "personal_info": {
            "full_name": "Adeel Tariq",
            "email": "adeel@example.com",
            "university": "FAST NUCES"
        },
        "experiences": []
    }

    file_content = b"Resume: Adeel Tariq, Email: adeel@example.com, Education: FAST NUCES"
    files = {"file": ("resume.txt", io.BytesIO(file_content), "text/plain")}

    with patch("app.services.extraction_service.query_groq_llm", new=AsyncMock(return_value=mock_extracted)):
        res = client.post(
            "/api/memory/upload-document",
            files=files,
            data={"user_id": 1, "auto_save": "true"}
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["saved"] is True
        assert data["extracted"]["personal_info"]["full_name"] == "Adeel Tariq"


def test_clear_memory(client):
    """Test clearing memory for user."""
    # Ensure memory exists
    client.post(
        "/api/users",
        json={}
    )
    client.post(
        "/api/users/1/personal-info",
        json={"full_name": "To Clear"}
    )

    del_res = client.delete("/api/memory/clear?user_id=1")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Current profile has null personal_info
    curr_res = client.get("/api/memory/current?user_id=1")
    assert curr_res.status_code == 200
    assert curr_res.json()["data"]["personal_info"] is None


def test_serve_dashboard_html(client):
    """Test that the web dashboard HTML is served at root /."""
    res = client.get("/")
    assert res.status_code == 200
    assert "Magic Fill" in res.text
    assert "text/html" in res.headers.get("content-type", "")
