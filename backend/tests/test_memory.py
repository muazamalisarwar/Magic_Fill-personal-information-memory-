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


def test_date_normalization():
    """Verify that dates in non-ISO formats (Year-only, Month Name Year, Present) normalize reliably."""
    from app.services.extraction_service import normalize_date_for_storage
    import datetime

    # Year only
    assert normalize_date_for_storage("2022", is_end_date=False) == datetime.date(2022, 1, 1)
    assert normalize_date_for_storage("2022", is_end_date=True) == datetime.date(2022, 12, 31)

    # Month Name Year
    assert normalize_date_for_storage("May 2023", is_end_date=False) == datetime.date(2023, 5, 1)
    assert normalize_date_for_storage("May 2023", is_end_date=True) == datetime.date(2023, 5, 31)
    assert normalize_date_for_storage("Sep 2021", is_end_date=False) == datetime.date(2021, 9, 1)

    # YYYY-MM
    assert normalize_date_for_storage("2024-03", is_end_date=False) == datetime.date(2024, 3, 1)
    assert normalize_date_for_storage("2024-03", is_end_date=True) == datetime.date(2024, 3, 31)

    # Standard ISO
    assert normalize_date_for_storage("2023-10-15", is_end_date=False) == datetime.date(2023, 10, 15)

    # Ongoing / Present
    assert normalize_date_for_storage("Present", is_end_date=True) is None
    assert normalize_date_for_storage("Current", is_end_date=True) is None
    assert normalize_date_for_storage(None, is_end_date=True) is None


@pytest.mark.anyio
async def test_repeated_upload_experience_upsert(client):
    """Verify that re-uploading the same experience updates it in place rather than duplicating."""
    mock_upload_1 = {
        "personal_info": {"full_name": "Test Candidate"},
        "experiences": [
            {
                "company": "Acme Corp",
                "job_title": "Software Engineer",
                "start_date": "2022",
                "end_date": "Present",
                "skills": "Python"
            }
        ],
        "custom_fields": []
    }

    mock_upload_2 = {
        "personal_info": {"full_name": "Test Candidate"},
        "experiences": [
            {
                "company": "Acme Corp",
                "job_title": "Software Engineer",
                "start_date": "2022-01-01",
                "end_date": "2024-05-01",
                "skills": "Python, TypeScript, FastAPI",
                "description": "Promoted and led cloud migration project"
            }
        ],
        "custom_fields": []
    }

    with patch("app.services.extraction_service.query_groq_llm", new=AsyncMock(return_value=mock_upload_1)):
        r1 = client.post(
            "/api/memory/extract-raw",
            json={"raw_text": "Experience at Acme Corp as Software Engineer...", "user_id": 99, "auto_save": True}
        )
        assert r1.status_code == 200
        exps1 = r1.json()["data"]["profile"]["experiences"]
        assert len(exps1) == 1
        assert exps1[0]["skills"] == "Python"

    # Second upload with updated details for same company & role
    with patch("app.services.extraction_service.query_groq_llm", new=AsyncMock(return_value=mock_upload_2)):
        r2 = client.post(
            "/api/memory/extract-raw",
            json={"raw_text": "Updated CV with Acme Corp lead role...", "user_id": 99, "auto_save": True}
        )
        assert r2.status_code == 200
        exps2 = r2.json()["data"]["profile"]["experiences"]
        # Must still be exactly 1 experience (updated in-place, NOT duplicated)
        assert len(exps2) == 1
        assert exps2[0]["skills"] == "Python, TypeScript, FastAPI"
        assert "cloud migration" in exps2[0]["description"]

