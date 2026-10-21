import pytest
from unittest.mock import patch, AsyncMock


def test_deterministic_field_matching(client):
    """
    Test deterministic matching of common website fields against user memory.
    Specifically tests:
    - First Name extracting 'Muazam' from 'Muazam Ali'
    - Last Name extracting 'Ali'
    - 'Institution Name' mapping to 'University of Education, Lahore'
    - Email, Phone, Company mappings
    """
    # 1. Create user
    user_res = client.post("/api/users", json={})
    user_id = user_res.json()["data"]["id"]

    # 2. Add personal info
    personal_payload = {
        "full_name": "Muazam Ali",
        "email": "muazam@example.com",
        "phone": "+92 300 1234567",
        "city": "Lahore",
        "university": "University of Education, Lahore",
        "degree": "BS Information Technology"
    }
    client.post(f"/api/users/{user_id}/personal-info", json=personal_payload)

    # 3. Add experience
    exp_payload = {
        "company": "Apex Software Solutions",
        "job_title": "Full Stack Engineer",
        "start_date": "2024-01-01"
    }
    client.post(f"/api/users/{user_id}/experiences", json=exp_payload)

    # 4. Form fields detected on a web page
    match_payload = {
        "user_id": user_id,
        "fields": [
            {"field_id": "input_fname", "label": "First Name", "name": "fname"},
            {"field_id": "input_lname", "label": "Last Name", "name": "lname"},
            {"field_id": "input_email", "label": "Email Address", "name": "email", "input_type": "email"},
            {"field_id": "input_phone", "label": "Contact Number", "name": "phone_num", "input_type": "tel"},
            {"field_id": "input_univ", "label": "Institution Name", "name": "institution_name"},
            {"field_id": "input_company", "label": "Current Employer", "name": "employer"},
            {"field_id": "input_unknown", "label": "Favorite Pet Name", "name": "pet_name"}
        ]
    }

    with patch("app.services.groq_service.query_groq_llm", new=AsyncMock(return_value=None)):
        res = client.post("/api/matching/fields", json=match_payload)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    # Verify counts
    assert data["total_detected"] == 7
    assert data["total_mapped"] == 6
    assert "input_unknown" in data["unresolved_fields"]

    mappings_by_id = {m["field_id"]: m for m in data["mappings"]}

    # Verify First Name does not contain full name
    assert mappings_by_id["input_fname"]["value"] == "Muazam"
    assert mappings_by_id["input_fname"]["memory_key"] == "personal_info.first_name"
    assert mappings_by_id["input_fname"]["source"] == "deterministic"

    # Verify Last Name
    assert mappings_by_id["input_lname"]["value"] == "Ali"
    assert mappings_by_id["input_lname"]["memory_key"] == "personal_info.last_name"

    # Verify Email & Phone
    assert mappings_by_id["input_email"]["value"] == "muazam@example.com"
    assert mappings_by_id["input_phone"]["value"] == "+92 300 1234567"

    # Verify Institution Name mapped to stored university
    assert mappings_by_id["input_univ"]["value"] == "University of Education, Lahore"
    assert mappings_by_id["input_univ"]["memory_key"] == "personal_info.university"

    # Verify Employer mapped to recent company
    assert mappings_by_id["input_company"]["value"] == "Apex Software Solutions"


def test_matching_non_existent_user(client):
    """Test matching against a non-existent user returns 404."""
    match_payload = {
        "user_id": 99999,
        "fields": [{"field_id": "f1", "label": "Full Name", "name": "fullname"}]
    }
    res = client.post("/api/matching/fields", json=match_payload)
    assert res.status_code == 404
    assert res.json()["error_code"] == "USER_NOT_FOUND"


def test_matching_with_empty_profile(client):
    """Test matching for a user with no personal info leaves fields unresolved."""
    user_res = client.post("/api/users", json={})
    user_id = user_res.json()["data"]["id"]

    match_payload = {
        "user_id": user_id,
        "fields": [
            {"field_id": "f1", "label": "Full Name", "name": "name"},
            {"field_id": "f2", "label": "Email", "name": "email"}
        ]
    }
    res = client.post("/api/matching/fields", json=match_payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_mapped"] == 0
    assert len(data["unresolved_fields"]) == 2


@pytest.mark.anyio
async def test_groq_llm_ambiguous_field_matching(client):
    """
    Test that ambiguous fields not resolved deterministically are passed to Groq
    and mapped if the returned value matches stored memory.
    """
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "Sarah Connor", "city": "Los Angeles"}
    )

    mock_llm_response = {
        "mappings": [
            {
                "field_id": "custom_q4",
                "memory_key": "personal_info.city",
                "value": "Los Angeles",
                "confidence": 0.88,
                "reason": "Field asks for resident municipality"
            }
        ]
    }

    match_payload = {
        "user_id": user_id,
        "fields": [
            {"field_id": "custom_q4", "label": "Municipality of Residence", "name": "f_mun"}
        ]
    }

    with patch("app.services.groq_service.query_groq_llm", new=AsyncMock(return_value=mock_llm_response)):
        res = client.post("/api/matching/fields", json=match_payload)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_mapped"] == 1
        mapping = data["mappings"][0]
        assert mapping["field_id"] == "custom_q4"
        assert mapping["value"] == "Los Angeles"
        assert mapping["source"] == "llm"


@pytest.mark.anyio
async def test_groq_llm_hallucination_protection(client):
    """
    Test that if the LLM invents a value not present in user memory,
    it is filtered out and the field remains unresolved.
    """
    user_id = client.post("/api/users", json={}).json()["data"]["id"]
    client.post(
        f"/api/users/{user_id}/personal-info",
        json={"full_name": "Sarah Connor"}
    )

    mock_hallucinated_response = {
        "mappings": [
            {
                "field_id": "f_fake",
                "memory_key": "personal_info.phone",
                "value": "+1 555 999 8888",  # Not in user memory!
                "confidence": 0.95,
                "reason": "Made up phone"
            }
        ]
    }

    match_payload = {
        "user_id": user_id,
        "fields": [
            {"field_id": "f_fake", "label": "Emergency Phone", "name": "emergency_phone"}
        ]
    }

    with patch("app.services.groq_service.query_groq_llm", new=AsyncMock(return_value=mock_hallucinated_response)):
        res = client.post("/api/matching/fields", json=match_payload)
        assert res.status_code == 200
        data = res.json()["data"]
        # The hallucinated value must be discarded
        assert data["total_mapped"] == 0
        assert "f_fake" in data["unresolved_fields"]


def test_matching_dropdown_dates_and_file_inputs(client):
    """
    Test matching for:
    - Dropdown menus (<select>) like Gender and Country
    - Abbreviated dropdown options (M / F)
    - Date inputs (<input type="date">) formatted to ISO YYYY-MM-DD
    - Photograph & CNIC file inputs (<input type="file">)
    """
    user_id = client.post("/api/users", json={}).json()["data"]["id"]

    photo_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    cnic_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    client.post(
        f"/api/users/{user_id}/personal-info",
        json={
            "full_name": "Hamza Tariq",
            "gender": "Male",
            "date_of_birth": "1999-11-04",
            "country": "Pakistan",
            "profile_photo": photo_uri,
            "cnic_photo": cnic_uri
        }
    )

    match_payload = {
        "user_id": user_id,
        "fields": [
            {
                "field_id": "sel_gender",
                "label": "Gender",
                "name": "gender",
                "input_type": "select-one",
                "options": ["Select Gender", "Male", "Female", "Other"]
            },
            {
                "field_id": "sel_gender_abbr",
                "label": "Sex",
                "name": "gender_code",
                "input_type": "select-one",
                "options": ["Select", "M", "F"]
            },
            {
                "field_id": "inp_dob",
                "label": "Date of Birth",
                "name": "birthdate",
                "input_type": "date"
            },
            {
                "field_id": "sel_country",
                "label": "Country / Nationality",
                "name": "country",
                "input_type": "select-one",
                "options": ["Choose...", "Australia", "Pakistan", "United Kingdom"]
            },
            {
                "field_id": "inp_photo",
                "label": "Passport Photograph / Headshot",
                "name": "avatar",
                "input_type": "file"
            },
            {
                "field_id": "inp_cnic_doc",
                "label": "Upload CNIC / National ID Card",
                "name": "id_document",
                "input_type": "file"
            }
        ]
    }

    res = client.post("/api/matching/fields", json=match_payload)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["total_detected"] == 6
    assert data["total_mapped"] == 6
    assert len(data["unresolved_fields"]) == 0

    mappings = {m["field_id"]: m for m in data["mappings"]}

    # Gender full word match
    assert mappings["sel_gender"]["value"] == "Male"
    assert mappings["sel_gender"]["memory_key"] == "personal_info.gender"

    # Gender abbreviated option match
    assert mappings["sel_gender_abbr"]["value"] == "M"

    # Date formatted YYYY-MM-DD
    assert mappings["inp_dob"]["value"] == "1999-11-04"
    assert mappings["inp_dob"]["memory_key"] == "personal_info.date_of_birth"

    # Country option match
    assert mappings["sel_country"]["value"] == "Pakistan"

    # Photo & CNIC document match
    assert mappings["inp_photo"]["value"] == photo_uri
    assert mappings["inp_photo"]["memory_key"] == "personal_info.profile_photo"
    assert mappings["inp_cnic_doc"]["value"] == cnic_uri
    assert mappings["inp_cnic_doc"]["memory_key"] == "personal_info.cnic_photo"


def test_salary_and_monthly_salary_matching(client):
    """
    Test that a custom field stored as 'Salary' correctly fills
    a form field requesting 'Monthly Salary' or 'Current Compensation'.
    """
    user_id = client.post("/api/users", json={}).json()["data"]["id"]

    # Add custom memory attribute 'Salary'
    cf_res = client.post(
        f"/api/users/{user_id}/custom-fields",
        json={
            "field_key": "salary",
            "field_label": "Salary",
            "field_value": "120,000 PKR",
            "category": "employment"
        }
    )
    assert cf_res.status_code == 201

    match_payload = {
        "user_id": user_id,
        "fields": [
            {
                "field_id": "f_monthly_sal",
                "label": "Monthly Salary",
                "name": "monthly_salary",
                "placeholder": "Enter monthly salary"
            },
            {
                "field_id": "f_curr_comp",
                "label": "Current Compensation",
                "name": "compensation",
                "placeholder": "Enter salary / compensation"
            }
        ]
    }

    res = client.post("/api/matching/fields", json=match_payload)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["total_detected"] == 2
    assert data["total_mapped"] == 2
    mappings = {m["field_id"]: m for m in data["mappings"]}

    assert mappings["f_monthly_sal"]["value"] == "120,000 PKR"
    assert mappings["f_monthly_sal"]["memory_key"] == "custom_fields.salary"
    assert mappings["f_curr_comp"]["value"] == "120,000 PKR"
    assert mappings["f_curr_comp"]["memory_key"] == "custom_fields.salary"


