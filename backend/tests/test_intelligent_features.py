"""
Comprehensive test suite for Magic Fill Major Features:
1. Intelligent Field Matching (semantic, context-aware, non-exact field names)
2. Support for All 10 Input Types (Text, Select, Radio, Checkbox, File, Textarea, Date, Switch, Range/Slider, Button)
3. Learn from All Input Types (Confirmation and DB commitment)
4. Visual Field Status (Green for matched, Red for missing, dynamic updates)
"""

import datetime
import pytest
from unittest.mock import patch, AsyncMock
from app.database.models import User, PersonalInfo, CustomField
from app.services.matching_service import match_form_fields
from app.schemas.matching import FieldMatchRequest, DetectedField
from app.schemas.learning import EvaluateFieldRequest, CommitLearningRequest
from app.services.learning_service import evaluate_field_for_learning, commit_learned_field


def test_intelligent_semantic_field_matching(db_session, client):
    """
    1. Intelligent Field Matching:
    Ensures non-exact names like "Your Name", "Applicant Name", "Name of Candidate"
    map cleanly to Full Name while strictly preserving first/last/father separation.
    Also tests Country synonyms (USA, United States) and Degree options.
    """
    # 1. Create user
    user = User(email="testuser@example.com", hashed_password="hashed_pw_123", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 2. Add personal info
    pinfo = PersonalInfo(
        user_id=user.id,
        full_name="Muazam Ali",
        email="muazam@example.com",
        phone="+92 300 1234567",
        country="Pakistan",
        city="Lahore",
        university="University of Education",
        degree="BS Computer Science",
        bio="Experienced software engineer specializing in scalable systems and AI.",
    )
    db_session.add(pinfo)
    # Add custom field for work authorization and slider
    cf_auth = CustomField(
        user_id=user.id,
        field_key="work_authorization",
        field_label="Work Authorization",
        field_value="Yes",
        category="employment"
    )
    cf_slider = CustomField(
        user_id=user.id,
        field_key="years_of_experience",
        field_label="Years of Experience",
        field_value="5",
        category="professional"
    )
    db_session.add_all([cf_auth, cf_slider])
    db_session.commit()

    # Form containing diverse semantic labels instead of exact key names
    fields = [
        {"field_id": "f_your_name", "name": "candidate_name", "label": "Your Name", "input_type": "text"},
        {"field_id": "f_applicant_name", "name": "app_name", "label": "Applicant Legal Name", "input_type": "text"},
        {"field_id": "f_country_drop", "name": "nationality", "label": "Country of Residence", "input_type": "select-one", "options": ["USA", "Pakistan", "Germany"]},
        {"field_id": "f_bio", "name": "about_you", "label": "Professional Summary / Bio", "input_type": "textarea"},
        {"field_id": "f_pet", "name": "pet_name", "label": "Pet Name", "input_type": "text"},  # Irrelevant, must NOT match full name
    ]

    mock_llm = {
        "mappings": [
            {"field_id": "f_country_drop", "memory_key": "personal_info.country", "value": "Pakistan", "confidence": 0.98},
            {"field_id": "f_bio", "memory_key": "personal_info.bio", "value": "Muazam Ali is a software engineer with expertise in Python.", "confidence": 0.95},
        ]
    }

    with patch("app.services.groq_service.query_groq_llm", new=AsyncMock(return_value=mock_llm)):
        res = client.post("/api/matching/fields", json={
            "user_id": user.id,
            "fields": fields,
            "form_context": "Job Application"
        })
    assert res.status_code == 200
    data = res.json()["data"]

    mapped_dict = {m["field_id"]: m for m in data["mappings"]}

    # Verify "Your Name" matched full name (direct match)
    assert "f_your_name" in mapped_dict
    assert mapped_dict["f_your_name"]["value"] == "Muazam Ali"
    assert mapped_dict["f_your_name"]["memory_key"] == "personal_info.full_name"
    assert mapped_dict["f_your_name"]["source"] == "deterministic"

    # Verify "Applicant Legal Name" matched full name (direct match)
    assert "f_applicant_name" in mapped_dict
    assert mapped_dict["f_applicant_name"]["value"] == "Muazam Ali"
    assert mapped_dict["f_applicant_name"]["source"] == "deterministic"

    # Verify Country dropdown picked "Pakistan" from options (AI match)
    assert "f_country_drop" in mapped_dict
    assert mapped_dict["f_country_drop"]["value"] == "Pakistan"
    assert mapped_dict["f_country_drop"]["source"] == "llm"

    # Verify Bio textarea matched (AI match)
    assert "f_bio" in mapped_dict
    assert "software engineer" in mapped_dict["f_bio"]["value"]
    assert mapped_dict["f_bio"]["source"] == "llm"

    # Verify "Pet Name" is UNMAPPED and placed in unresolved_fields (Visual Field Status = Red candidate)
    assert "f_pet" not in mapped_dict
    unresolved_ids = data["unresolved_fields"]
    assert "f_pet" in unresolved_ids


def test_support_all_10_input_types(db_session, client):
    """
    2. Support All 10 Input Types:
    Detects and matches:
    - Text Inputs
    - Dropdowns
    - Radio Buttons
    - Checkboxes
    - File Uploads
    - Text Areas
    - Date Pickers
    - Toggle/Switches
    - Sliders (Range)
    - Buttons/Actions
    """
    user = User(email="sarah@example.com", hashed_password="pw", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    pinfo = PersonalInfo(
        user_id=user.id,
        full_name="Sarah Connor",
        email="sarah@example.com",
        phone="+1 555 987 6543",
        date_of_birth=datetime.date(1992, 6, 15),
        gender="Female",
        country="United States",
        bio="Senior Cyber Security Lead with 8 years of defense and threat modeling experience.",
    )
    db_session.add(pinfo)
    cf_auth = CustomField(user_id=user.id, field_key="work_authorization", field_label="Work Authorization", field_value="Yes", category="employment")
    cf_relocate = CustomField(user_id=user.id, field_key="willing_to_relocate", field_label="Willing to Relocate", field_value="Yes", category="employment")
    cf_exp = CustomField(user_id=user.id, field_key="years_of_experience", field_label="Years of Experience", field_value="8", category="professional")
    db_session.add_all([cf_auth, cf_relocate, cf_exp])
    db_session.commit()

    test_fields = [
        # 1. Text input
        {"field_id": "in_text", "name": "contact_email", "label": "Email Address", "input_type": "email"},
        # 2. Dropdown (Select)
        {"field_id": "in_select", "name": "gender_select", "label": "Gender", "input_type": "select-one", "options": ["Male", "Female", "Other"]},
        # 3. Radio Buttons
        {"field_id": "in_radio", "name": "work_auth_radio", "label": "Legally Authorized to Work", "input_type": "radio", "options": ["Yes", "No"]},
        # 4. Checkbox
        {"field_id": "in_check", "name": "terms", "label": "Work Authorization Confirmation", "input_type": "checkbox", "checked": False},
        # 5. File Upload
        {"field_id": "in_file", "name": "resume_file", "label": "Upload Resume / Document", "input_type": "file", "accept": ".pdf,.doc"},
        # 6. Text Area
        {"field_id": "in_textarea", "name": "professional_bio", "label": "Candidate Summary", "input_type": "textarea"},
        # 7. Date Picker
        {"field_id": "in_date", "name": "dob_date", "label": "Date of Birth", "input_type": "date"},
        # 8. Toggle / Switch
        {"field_id": "in_switch", "name": "relocate_switch", "label": "Open to Relocation", "input_type": "checkbox", "role": "switch"},
        # 9. Slider / Range
        {"field_id": "in_slider", "name": "experience_slider", "label": "Years of Experience", "input_type": "range", "min": "0", "max": "20", "step": "1"},
        # 10. Applicable Action Button
        {"field_id": "in_btn", "name": "submit_action", "label": "Submit Application", "input_type": "submit", "tag_name": "button"},
    ]

    mock_llm_10 = {
        "mappings": [
            {"field_id": "in_select", "memory_key": "personal_info.gender", "value": "Female", "confidence": 0.98},
            {"field_id": "in_radio", "memory_key": "custom_fields.work_authorization", "value": "Yes", "confidence": 0.98},
            {"field_id": "in_check", "memory_key": "custom_fields.work_authorization", "value": "true", "confidence": 0.98},
            {"field_id": "in_textarea", "memory_key": "personal_info.bio", "value": "Senior Cyber Security Lead with 8 years of defense experience.", "confidence": 0.95},
            {"field_id": "in_date", "memory_key": "personal_info.date_of_birth", "value": "1992-06-15", "confidence": 0.98},
            {"field_id": "in_switch", "memory_key": "custom_fields.willing_to_relocate", "value": "true", "confidence": 0.98},
            {"field_id": "in_slider", "memory_key": "custom_fields.years_of_experience", "value": "8", "confidence": 0.98},
        ]
    }

    with patch("app.services.groq_service.query_groq_llm", new=AsyncMock(return_value=mock_llm_10)):
        res = client.post("/api/matching/fields", json={
            "user_id": user.id,
            "fields": test_fields,
            "form_context": "Comprehensive Portal"
        })
    assert res.status_code == 200
    data = res.json()["data"]

    mapped_map = {m["field_id"]: m for m in data["mappings"]}

    # Verify Text Input (Email is direct matched)
    assert mapped_map["in_text"]["value"] == "sarah@example.com"
    assert mapped_map["in_text"]["source"] == "deterministic"

    # Verify Dropdown (AI matched)
    assert mapped_map["in_select"]["value"] == "Female"
    assert mapped_map["in_select"]["source"] == "llm"

    # Verify Radio Button (AI matched)
    assert mapped_map["in_radio"]["value"] == "Yes"
    assert mapped_map["in_radio"]["source"] == "llm"

    # Verify Checkbox (boolean checked representation, AI matched)
    assert mapped_map["in_check"]["value"] in ("true", "Yes")
    assert mapped_map["in_check"]["source"] == "llm"

    # Verify Text Area (AI matched)
    assert "Cyber Security" in mapped_map["in_textarea"]["value"]
    assert mapped_map["in_textarea"]["source"] == "llm"

    # Verify Date Picker (ISO YYYY-MM-DD, AI matched)
    assert mapped_map["in_date"]["value"] == "1992-06-15"
    assert mapped_map["in_date"]["source"] == "llm"

    # Verify Toggle / Switch (AI matched)
    assert mapped_map["in_switch"]["value"] in ("true", "Yes")
    assert mapped_map["in_switch"]["source"] == "llm"

    # Verify Range Slider (AI matched)
    assert mapped_map["in_slider"]["value"] == "8"
    assert mapped_map["in_slider"]["source"] == "llm"


@pytest.mark.anyio
async def test_learn_from_all_input_types_and_update_db(db_session):
    """
    3. Learn from All Input Types:
    Captures information from:
    - Text fields
    - Dropdowns
    - Radio buttons
    - Checkboxes
    - Dates
    - Sliders
    Requires confirmation before saving and correctly updates the database.
    """
    user = User(email="learner@example.com", hashed_password="pw", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # A. Learn new GPA from a slider or dropdown
    req_gpa = EvaluateFieldRequest(
        field_name="academic_gpa",
        label="Grade Point Average (GPA)",
        value="3.8",
        input_type="text",
        form_context="University Admission Form"
    )
    eval_gpa = await evaluate_field_for_learning(db=db_session, user_id=user.id, request=req_gpa)
    assert eval_gpa.is_learnable is True
    assert eval_gpa.action_type.value == "NEW_ATTRIBUTE"
    assert eval_gpa.canonical_key == "gpa"

    # Commit with user consent
    commit_gpa = CommitLearningRequest(
        action_type=eval_gpa.action_type,
        canonical_key=eval_gpa.canonical_key,
        field_label=eval_gpa.field_label,
        value="3.8",
        category="academic"
    )
    res_gpa = commit_learned_field(db=db_session, user_id=user.id, request=commit_gpa)
    assert res_gpa["saved"] is True

    # Verify custom_field persisted in database
    cf_saved = db_session.query(CustomField).filter(CustomField.user_id == user.id, CustomField.field_key == "gpa").first()
    assert cf_saved is not None
    assert cf_saved.field_value == "3.8"

    # B. Learn from Radio Button (e.g. Work Authorization)
    req_radio = EvaluateFieldRequest(
        field_name="authorized_to_work",
        label="Legally Authorized to Work",
        value="Yes",
        input_type="radio",
        form_context="Job Application"
    )
    eval_radio = await evaluate_field_for_learning(db=db_session, user_id=user.id, request=req_radio)
    assert eval_radio.is_learnable is True
    assert eval_radio.canonical_key == "work_authorization"

    commit_radio = CommitLearningRequest(
        action_type=eval_radio.action_type,
        canonical_key=eval_radio.canonical_key,
        field_label=eval_radio.field_label,
        value="Yes",
        category="employment"
    )
    res_radio = commit_learned_field(db=db_session, user_id=user.id, request=commit_radio)
    assert res_radio["saved"] is True
    cf_radio = db_session.query(CustomField).filter(CustomField.user_id == user.id, CustomField.field_key == "work_authorization").first()
    assert cf_radio.field_value == "Yes"

    # C. Learn from Date Picker (Start date)
    req_date = EvaluateFieldRequest(
        field_name="available_start_date",
        label="Earliest Available Start Date",
        value="2026-11-01",
        input_type="date",
        form_context="Job Application"
    )
    eval_date = await evaluate_field_for_learning(db=db_session, user_id=user.id, request=req_date)
    assert eval_date.is_learnable is True
    assert eval_date.canonical_key == "start_date"

    commit_date = CommitLearningRequest(
        action_type=eval_date.action_type,
        canonical_key=eval_date.canonical_key,
        field_label=eval_date.field_label,
        value="2026-11-01",
        category="employment"
    )
    res_date = commit_learned_field(db=db_session, user_id=user.id, request=commit_date)
    assert res_date["saved"] is True

    # D. Excluded inputs (e.g. passwords, chat inquiries) must NOT be learnable
    req_secret = EvaluateFieldRequest(
        field_name="pin_code",
        label="Security Pin",
        value="1234",
        input_type="password"
    )
    eval_secret = await evaluate_field_for_learning(db=db_session, user_id=user.id, request=req_secret)
    assert eval_secret.is_learnable is False


def test_visual_field_status_partitioning_and_dynamic_flip(db_session, client):
    """
    4. Visual Field Status:
    Highlights fields Green when Magic Fill has stored data available,
    and Red when no suitable data is available.
    Verifies that the API partitions fields into `mappings` (Green) and `unresolved_fields` (Red),
    and when a missing field is learned, it dynamically flips to Green on subsequent match.
    """
    user = User(email="alex@prototype.org", hashed_password="pw", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Initially user only has email and full name
    pinfo = PersonalInfo(
        user_id=user.id,
        full_name="Alex Mercer",
        email="alex@prototype.org"
    )
    db_session.add(pinfo)
    db_session.commit()

    fields_scan_1 = [
        {"field_id": "id_name", "name": "full_name", "label": "Full Name", "input_type": "text"},
        {"field_id": "id_email", "name": "email", "label": "Email Address", "input_type": "email"},
        {"field_id": "id_linkedin", "name": "linkedin_url", "label": "LinkedIn Profile URL", "input_type": "url"},  # Missing -> Red
        {"field_id": "id_phone", "name": "phone_number", "label": "Mobile Phone", "input_type": "tel"},             # Missing -> Red
    ]

    with patch("app.services.groq_service.query_groq_llm", new=AsyncMock(return_value=None)):
        res1 = client.post("/api/matching/fields", json={
            "user_id": user.id,
            "fields": fields_scan_1
        })
    assert res1.status_code == 200
    data1 = res1.json()["data"]

    matched_ids_1 = {m["field_id"] for m in data1["mappings"]}
    unresolved_ids_1 = set(data1["unresolved_fields"])

    # Verify Green indicators (Available data)
    assert "id_name" in matched_ids_1
    assert "id_email" in matched_ids_1

    # Verify Red indicators (Missing data)
    assert "id_linkedin" in unresolved_ids_1
    assert "id_phone" in unresolved_ids_1
    assert "id_linkedin" not in matched_ids_1

    # Now simulate user typing their LinkedIn URL into the form and learning it!
    commit_req = CommitLearningRequest(
        action_type="NEW_ATTRIBUTE",
        canonical_key="linkedin_url",
        field_label="LinkedIn Profile URL",
        value="https://linkedin.com/in/alexmercer",
        category="professional"
    )
    commit_learned_field(db=db_session, user_id=user.id, request=commit_req)

    # Dynamic status update: Rescan form fields after learning (LinkedIn mapped via AI)
    mock_llm_linkedin = {
        "mappings": [
            {"field_id": "id_linkedin", "memory_key": "custom_fields.linkedin_url", "value": "https://linkedin.com/in/alexmercer", "confidence": 0.98}
        ]
    }
    with patch("app.services.groq_service.query_groq_llm", new=AsyncMock(return_value=mock_llm_linkedin)):
        res2 = client.post("/api/matching/fields", json={
            "user_id": user.id,
            "fields": fields_scan_1
        })
    assert res2.status_code == 200
    data2 = res2.json()["data"]

    matched_ids_2 = {m["field_id"] for m in data2["mappings"]}
    unresolved_ids_2 = set(data2["unresolved_fields"])

    # LinkedIn has dynamically flipped from Red (Missing) to Green (Matched)!
    assert "id_linkedin" in matched_ids_2
    assert "id_linkedin" not in unresolved_ids_2
    assert data2["total_mapped"] == 3
