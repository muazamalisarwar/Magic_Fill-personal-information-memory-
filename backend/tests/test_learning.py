import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.learning import FieldCategory, LearningActionType
from app.services.learning_service import classify_field_deterministically


# =============================================================================
# 1. Unit Tests: Field Classification (Deterministic & Semantic)
# =============================================================================

def test_classify_new_linkedin_url():
    """Test that a LinkedIn URL field is classified as PROFESSIONAL_INFO."""
    cat, canon_k, lbl, sub_cat = classify_field_deterministically(
        field_name="linkedin_url",
        label="LinkedIn Profile URL",
        value="https://linkedin.com/in/muazamali"
    )
    assert cat == FieldCategory.PROFESSIONAL_INFO
    assert canon_k == "linkedin_url"
    assert lbl == "LinkedIn Profile URL"


def test_classify_new_certification():
    """Test that a certification input is classified as PROFESSIONAL_INFO."""
    cat, canon_k, lbl, sub_cat = classify_field_deterministically(
        field_name="cert_name",
        label="Professional Certifications & Licenses",
        value="AWS Certified Solutions Architect"
    )
    assert cat == FieldCategory.PROFESSIONAL_INFO
    assert canon_k == "certifications"


def test_classify_chatgpt_message_field():
    """Test that ChatGPT / AI prompt inputs are classified as COMMUNICATION_CONTENT and excluded."""
    cat, canon_k, lbl, sub_cat = classify_field_deterministically(
        field_name="chat_prompt",
        label="Ask a question or enter your message prompt",
        value="Can you explain quantum computing in simple terms?",
        input_type="textarea"
    )
    assert cat == FieldCategory.COMMUNICATION_CONTENT
    assert canon_k is None


def test_classify_search_bar():
    """Test that search queries are classified as TRANSACTIONAL and excluded."""
    cat, canon_k, lbl, sub_cat = classify_field_deterministically(
        field_name="search_query",
        label="Search Products or Jobs",
        value="Software Engineer in Lahore",
        input_type="text"
    )
    assert cat == FieldCategory.TRANSACTIONAL
    assert canon_k is None


def test_classify_contact_us_textarea():
    """Test that contact-us support message textareas are classified as COMMUNICATION_CONTENT."""
    cat, canon_k, lbl, sub_cat = classify_field_deterministically(
        field_name="contact_message",
        label="Leave your inquiry or support feedback",
        value="Hello, I have an issue with my recent invoice payment.",
        input_type="textarea"
    )
    assert cat == FieldCategory.COMMUNICATION_CONTENT
    assert canon_k is None


def test_classify_password_or_otp_field():
    """Test that password, OTP, and secret fields are classified as SENSITIVE_OR_SECRET and never captured."""
    # Password
    cat1, _, _, _ = classify_field_deterministically(
        field_name="user_password",
        label="Enter Password",
        value="Secret123!",
        input_type="password"
    )
    assert cat1 == FieldCategory.SENSITIVE_OR_SECRET

    # OTP
    cat2, _, _, _ = classify_field_deterministically(
        field_name="otp_code",
        label="Two-Factor Authentication OTP Verification Code",
        value="849201",
        input_type="text"
    )
    assert cat2 == FieldCategory.SENSITIVE_OR_SECRET


def test_classify_unknown_generic_textarea():
    """Test that generic, ambiguous textareas default to UNKNOWN."""
    cat, canon_k, lbl, sub_cat = classify_field_deterministically(
        field_name="custom_txt_99",
        label="Custom Field",
        value="Lorem ipsum dolor",
        input_type="text"
    )
    assert cat == FieldCategory.UNKNOWN


def test_classify_empty_or_placeholder_value():
    """Test that empty or placeholder values are rejected and marked UNKNOWN."""
    cat1, _, _, _ = classify_field_deterministically(
        field_name="email",
        label="Email Address",
        value=""
    )
    assert cat1 == FieldCategory.UNKNOWN

    cat2, _, _, _ = classify_field_deterministically(
        field_name="email",
        label="Email Address",
        value="N/A"
    )
    assert cat2 == FieldCategory.UNKNOWN


# =============================================================================
# 2. Integration Tests: API /api/memory/evaluate-field
# =============================================================================

def test_evaluate_new_linkedin_url(client):
    """
    Scenario: User fills out a new LinkedIn Profile URL not in their memory.
    Expected: Ask whether to save (is_learnable=True, action_type=NEW_ATTRIBUTE).
    """
    # 1. Register user
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "muazam.dev@example.com", "password": "Password123!", "full_name": "Muazam Ali"}
    )
    token = reg_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Evaluate LinkedIn URL
    payload = {
        "field_name": "linkedin_profile",
        "label": "LinkedIn Profile URL",
        "value": "https://linkedin.com/in/muazam-ali",
        "input_type": "url"
    }
    res = client.post("/api/memory/evaluate-field", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["is_learnable"] is True
    assert data["action_type"] == LearningActionType.NEW_ATTRIBUTE
    assert data["canonical_key"] == "linkedin_url"
    assert data["field_label"] == "LinkedIn Profile URL"
    assert data["new_value"] == "https://linkedin.com/in/muazam-ali"


def test_evaluate_existing_email_different_label_no_duplicate(client):
    """
    Scenario: Existing email under a different field label (e.g. 'Work Email' or 'Communication Email').
    Expected: No duplicate suggestion (is_learnable=False, action_type=NO_ACTION).
    """
    # 1. Register user with email
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "sarah.connor@example.com", "password": "Password123!", "full_name": "Sarah Connor"}
    )
    token = reg_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Candidate input enters the same email under a different label
    payload = {
        "field_name": "comm_email",
        "label": "Primary Contact Email Address",
        "value": "sarah.connor@example.com",
        "input_type": "email"
    }
    res = client.post("/api/memory/evaluate-field", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["is_learnable"] is False
    assert data["action_type"] == LearningActionType.NO_ACTION
    assert "already saved" in data["reason"].lower()


def test_evaluate_changed_phone_number_triggers_update(client):
    """
    Scenario: User enters a changed phone number.
    Expected: Ask whether to update (is_learnable=True, action_type=UPDATE_ATTRIBUTE).
    """
    # 1. Register user
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "john.wick@example.com", "password": "Password123!", "full_name": "John Wick"}
    )
    user_id = reg_res.json()["data"]["user"]["id"]
    token = reg_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Set existing phone
    client.put(
        f"/api/users/{user_id}/personal-info",
        json={"phone": "+92 300 1111111"},
        headers=auth_headers
    )

    # 2. Candidate input has a DIFFERENT phone number
    payload = {
        "field_name": "mobile_phone",
        "label": "Cell Number",
        "value": "+92 321 9999999",
        "input_type": "tel"
    }
    res = client.post("/api/memory/evaluate-field", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["is_learnable"] is True
    assert data["action_type"] == LearningActionType.UPDATE_ATTRIBUTE
    assert data["canonical_key"] == "phone"
    assert data["existing_value"] == "+92 300 1111111"
    assert data["new_value"] == "+92 321 9999999"


def test_evaluate_excluded_fields(client):
    """
    Scenario: User fills out search bars, chat messages, support textareas, or password fields.
    Expected: NEVER ask to save (is_learnable=False).
    """
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "user.testing@example.com", "password": "Password123!", "full_name": "Tester"}
    )
    token = reg_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. ChatGPT message
    r1 = client.post(
        "/api/memory/evaluate-field",
        json={"field_name": "chat_input", "label": "Ask AI anything", "value": "How to learn python fast?"},
        headers=auth_headers
    )
    assert r1.json()["data"]["is_learnable"] is False

    # 2. Search query
    r2 = client.post(
        "/api/memory/evaluate-field",
        json={"field_name": "search_box", "label": "Search across jobs", "value": "Backend Developer"},
        headers=auth_headers
    )
    assert r2.json()["data"]["is_learnable"] is False

    # 3. Contact Us comment
    r3 = client.post(
        "/api/memory/evaluate-field",
        json={"field_name": "comments", "label": "Leave your message", "value": "Please call me back regarding my order.", "input_type": "textarea"},
        headers=auth_headers
    )
    assert r3.json()["data"]["is_learnable"] is False

    # 4. OTP / Verification code
    r4 = client.post(
        "/api/memory/evaluate-field",
        json={"field_name": "verification_code", "label": "Enter 6-digit OTP code", "value": "123456"},
        headers=auth_headers
    )
    assert r4.json()["data"]["is_learnable"] is False


# =============================================================================
# 3. Integration Tests: Committing Approved Learning to Database
# =============================================================================

def test_commit_new_attribute_saves_and_enables_autofill(client):
    """
    Scenario: User approves saving a new attribute (LinkedIn Profile URL).
    Expected:
    1. Saved in user's records.
    2. Immediately available in user profile.
    3. Future autofill matching maps this field!
    """
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "alex.dev@example.com", "password": "Password123!", "full_name": "Alex Mercer"}
    )
    user_id = reg_res.json()["data"]["user"]["id"]
    token = reg_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. Commit learning
    commit_payload = {
        "action_type": LearningActionType.NEW_ATTRIBUTE,
        "canonical_key": "linkedin_url",
        "field_label": "LinkedIn Profile URL",
        "value": "https://linkedin.com/in/alex-mercer",
        "category": "social"
    }
    commit_res = client.post("/api/memory/commit-learning", json=commit_payload, headers=auth_headers)
    assert commit_res.status_code == 200
    assert commit_res.json()["data"]["saved"] is True

    # 2. Verify stored in profile
    profile_res = client.get(f"/api/users/{user_id}/profile", headers=auth_headers)
    assert profile_res.status_code == 200
    custom_fields = profile_res.json()["data"]["custom_fields"]
    assert any(cf["field_key"] == "linkedin_url" and cf["field_value"] == "https://linkedin.com/in/alex-mercer" for cf in custom_fields)

    # 3. Verify future autofill matching uses this newly learned attribute
    match_payload = {
        "user_id": user_id,
        "fields": [
            {"field_id": "inp_li", "label": "LinkedIn Profile URL", "name": "linkedin"}
        ]
    }
    match_res = client.post("/api/matching/fields", json=match_payload, headers=auth_headers)
    assert match_res.status_code == 200
    mappings = {m["field_id"]: m for m in match_res.json()["data"]["mappings"]}
    assert mappings["inp_li"]["value"] == "https://linkedin.com/in/alex-mercer"


def test_commit_update_attribute_modifies_saved_data(client):
    """
    Scenario: User approves updating an existing attribute (phone number).
    Expected: Phone number is updated in database.
    """
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "taha.k@example.com", "password": "Password123!", "full_name": "Taha Khan"}
    )
    user_id = reg_res.json()["data"]["user"]["id"]
    token = reg_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Create initial personal info phone
    client.put(
        f"/api/users/{user_id}/personal-info",
        json={"phone": "+92 300 1111111"},
        headers=auth_headers
    )

    # Commit update
    commit_payload = {
        "action_type": LearningActionType.UPDATE_ATTRIBUTE,
        "canonical_key": "phone",
        "field_label": "Phone Number",
        "value": "+92 321 8888888"
    }
    commit_res = client.post("/api/memory/commit-learning", json=commit_payload, headers=auth_headers)
    assert commit_res.status_code == 200
    assert commit_res.json()["data"]["saved"] is True

    # Verify updated
    pinfo_res = client.get(f"/api/users/{user_id}/personal-info", headers=auth_headers)
    assert pinfo_res.json()["data"]["phone"] == "+92 321 8888888"


# =============================================================================
# 4. Multi-User Isolation & Security Tests
# =============================================================================

def test_multi_user_isolation_never_leaks_or_overwrites(client):
    """
    Scenario: Another user is signed in.
    Expected: Never expose or update the previous user's memory.
    """
    # User 1 (Alice)
    alice_res = client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "password": "Password123!", "full_name": "Alice"}
    )
    alice_token = alice_res.json()["data"]["access_token"]
    alice_id = alice_res.json()["data"]["user"]["id"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    client.post(
        "/api/memory/commit-learning",
        json={"action_type": LearningActionType.NEW_ATTRIBUTE, "canonical_key": "portfolio_url", "field_label": "Portfolio", "value": "https://alice.dev"},
        headers=alice_headers
    )

    # User 2 (Bob)
    bob_res = client.post(
        "/api/auth/register",
        json={"email": "bob@example.com", "password": "Password123!", "full_name": "Bob"}
    )
    bob_token = bob_res.json()["data"]["access_token"]
    bob_id = bob_res.json()["data"]["user"]["id"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # Bob evaluates portfolio URL
    bob_eval = client.post(
        "/api/memory/evaluate-field",
        json={"field_name": "portfolio", "label": "Portfolio URL", "value": "https://bob.dev"},
        headers=bob_headers
    )
    # Bob should see it as a NEW attribute, NOT an update of Alice's portfolio!
    assert bob_eval.json()["data"]["action_type"] == LearningActionType.NEW_ATTRIBUTE

    # Bob commits his own portfolio
    client.post(
        "/api/memory/commit-learning",
        json={"action_type": LearningActionType.NEW_ATTRIBUTE, "canonical_key": "portfolio_url", "field_label": "Portfolio", "value": "https://bob.dev"},
        headers=bob_headers
    )

    # Verify Alice's portfolio is untouched
    alice_profile = client.get(f"/api/users/{alice_id}/profile", headers=alice_headers).json()["data"]
    assert any(cf["field_value"] == "https://alice.dev" for cf in alice_profile["custom_fields"])
    assert not any(cf["field_value"] == "https://bob.dev" for cf in alice_profile["custom_fields"])

    # Verify Bob's portfolio has Bob's data
    bob_profile = client.get(f"/api/users/{bob_id}/profile", headers=bob_headers).json()["data"]
    assert any(cf["field_value"] == "https://bob.dev" for cf in bob_profile["custom_fields"])
    assert not any(cf["field_value"] == "https://alice.dev" for cf in bob_profile["custom_fields"])
