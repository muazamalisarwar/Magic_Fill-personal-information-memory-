"""
Magic Fill - AI Memory Copilot Unit & Integration Tests
Tests conversational Q&A grounded in memory vault and real-time updates.
"""

import datetime
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import User, PersonalInfo, CustomField, Experience


@pytest.fixture
def seed_user_data(db_session: Session):
    """Seed test user #1 with comprehensive memory records."""
    user = User(id=1, email="muazam@example.com", full_name="Muazam Ali")
    db_session.add(user)
    p_info = PersonalInfo(
        user_id=1,
        full_name="Muazam Ali",
        email="muazam@example.com",
        phone="0326-8848703",
        degree="Bachelor of Science in Computer Science",
        university="Stanford University",
        department="Computer Science & Engineering",
        graduation_year=2024
    )
    db_session.add(p_info)
    exp = Experience(
        user_id=1,
        company="Tech Corp",
        job_title="Software Engineer",
        start_date=datetime.date(2022, 1, 1),
        end_date=datetime.date(2024, 1, 1),
        skills="Python, FastAPI, TypeScript"
    )
    db_session.add(exp)
    db_session.commit()
    return user


def test_copilot_query_educational_experiences_local(client: TestClient, seed_user_data):
    """Verify asking about education returns grounded degrees and university via grounded fallback."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "What are my educational experiences?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["intent"] == "QUERY"
        reply = data["data"]["reply"]
        assert "Bachelor of Science in Computer Science" in reply
        assert "Stanford University" in reply
        assert len(data["data"]["updates"]) == 0


def test_copilot_query_contact_information_local(client: TestClient, seed_user_data):
    """Verify asking about contact details returns saved phone and email via grounded fallback."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "What contact info do you have for me?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "0326-8848703" in data["data"]["reply"]
        assert "muazam@example.com" in data["data"]["reply"]


def test_copilot_update_name_local(client: TestClient, db_session: Session, seed_user_data):
    """Verify that instructing copilot to update name updates database records."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "Update my name to Muazam Ali Sarwar"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["intent"] == "UPDATE"
        assert len(data["data"]["updates"]) > 0
        upd = data["data"]["updates"][0]
        assert upd["key"] == "full_name"
        assert "Muazam Ali Sarwar" in upd["new_value"]

        # Verify directly in SQLite DB session
        db_session.expire_all()
        user = db_session.query(User).filter(User.id == 1).first()
        p_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
        assert user.full_name == "Muazam Ali Sarwar"
        assert p_info.full_name == "Muazam Ali Sarwar"


def test_copilot_update_phone_local(client: TestClient, db_session: Session, seed_user_data):
    """Verify updating phone persists to personal_info."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "Change my phone number to +92 300 1234567"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["intent"] == "UPDATE"

        db_session.expire_all()
        p_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
        assert "+92 300 1234567" in p_info.phone


def test_copilot_add_skill_local(client: TestClient, db_session: Session, seed_user_data):
    """Verify adding a new skill adds custom_field."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "Add a new skill: Next.js and Tailwind CSS"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["intent"] == "UPDATE"
        assert len(data["data"]["updates"]) > 0

        db_session.expire_all()
        cfs = db_session.query(CustomField).filter(CustomField.user_id == 1).all()
        assert any("Next.js" in (cf.field_value or "") for cf in cfs)


def test_copilot_with_mocked_llm_query(client: TestClient, seed_user_data):
    """Verify LLM query response is rendered directly."""
    mock_llm_output = {
        "intent": "QUERY",
        "reply": "Your educational credentials from Stanford University include a Bachelor of Science in Computer Science, completed in 2024.",
        "updates": []
    }
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=mock_llm_output)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "Tell me about my Stanford degree"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["intent"] == "QUERY"
        assert "Stanford University" in data["data"]["reply"]


def test_copilot_with_mocked_llm_update(client: TestClient, db_session: Session, seed_user_data):
    """Verify copilot applies LLM-instructed structured updates to database."""
    mock_llm_output = {
        "intent": "UPDATE",
        "reply": "I have updated your contact email address to 'dev@muazam.pro'.",
        "updates": [
            {
                "field_type": "personal_info",
                "key": "email",
                "label": "Contact Email",
                "old_value": "muazam@example.com",
                "new_value": "dev@muazam.pro",
                "action": "UPDATE"
            }
        ]
    }
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=mock_llm_output)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "Update my email to dev@muazam.pro"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["intent"] == "UPDATE"
        assert "dev@muazam.pro" in data["data"]["reply"]

        db_session.expire_all()
        p_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
        assert p_info.email == "dev@muazam.pro"


def test_copilot_update_address_typo_tolerant_local(client: TestClient, db_session: Session, seed_user_data):
    """Verify updating address with typo 'chnage' persists to personal_info."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "chnage my address to Narang Manid zafar street, Lahore Pakistan"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["intent"] == "UPDATE"
        assert len(data["data"]["updates"]) > 0

        db_session.expire_all()
        p_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
        assert "Narang Manid zafar street" in p_info.address


def test_copilot_save_custom_attribute_local(client: TestClient, db_session: Session, seed_user_data):
    """Verify natural statements like 'my favorite fruit is mango' save as custom fields."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "my favroite fruit is mango"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["intent"] == "UPDATE"

        db_session.expire_all()
        cfs = db_session.query(CustomField).filter(CustomField.user_id == 1).all()
        assert any(cf.field_value == "mango" for cf in cfs)


def test_copilot_query_saved_name_local(client: TestClient, seed_user_data):
    """Verify query 'what is currently saved my name' returns user's name."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "what is currently saved my name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["intent"] == "QUERY"
        assert "Muazam Ali" in data["data"]["reply"]


def test_copilot_query_address_local(client: TestClient, db_session: Session, seed_user_data):
    """Verify query 'what address you know about me' returns user's address."""
    p_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
    p_info.address = "123 Main Street, Lahore"
    db_session.commit()

    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        response = client.post(
            "/api/memory/copilot-chat",
            json={"message": "what address you know about me"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["intent"] == "QUERY"
        assert "Lahore" in data["data"]["reply"]


def test_copilot_multi_turn_update_to_address_local(client: TestClient, db_session: Session, seed_user_data):
    """Verify multi-turn: 'what is my current address saved' -> 'update to Narang Mandi zafar street, Lahore'."""
    p_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
    p_info.address = "Lahore, Pakistan"
    db_session.commit()

    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        # Turn 1
        r1 = client.post(
            "/api/memory/copilot-chat",
            json={"message": "whats my current address saved"}
        )
        assert r1.status_code == 200
        reply1 = r1.json()["data"]["reply"]

        # Turn 2: User doesn't say 'address', just says 'update to Narang Mandi zafar street, Lahore'
        r2 = client.post(
            "/api/memory/copilot-chat",
            json={
                "message": "update to Narang Mandi zafar street, Lahore",
                "history": [
                    {"role": "user", "content": "whats my current address saved"},
                    {"role": "assistant", "content": reply1}
                ]
            }
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["success"] is True
        assert data2["data"]["intent"] == "UPDATE"
        assert len(data2["data"]["updates"]) > 0
        assert data2["data"]["updates"][0]["key"] == "address"

        db_session.expire_all()
        p_info_after = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
        assert "Narang Mandi zafar street" in p_info_after.address


def test_copilot_multi_turn_phone_update_local(client: TestClient, db_session: Session, seed_user_data):
    """Verify multi-turn: 'what is my phone number' -> 'update to 0300-9998877'."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        # Turn 1
        r1 = client.post(
            "/api/memory/copilot-chat",
            json={"message": "what is my phone number"}
        )
        assert r1.status_code == 200
        assert "0326-8848703" in r1.json()["data"]["reply"]

        # Turn 2: User says 'change to 0300-9998877'
        r2 = client.post(
            "/api/memory/copilot-chat",
            json={
                "message": "change to 0300-9998877",
                "history": [
                    {"role": "user", "content": "what is my phone number"},
                    {"role": "assistant", "content": r1.json()["data"]["reply"]}
                ]
            }
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["data"]["intent"] == "UPDATE"
        assert any(u["key"] == "phone" for u in data2["data"]["updates"])

        db_session.expire_all()
        p_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
        assert p_info.phone == "0300-9998877"


def test_copilot_multi_turn_degree_update_local(client: TestClient, db_session: Session, seed_user_data):
    """Verify multi-turn: 'what degree is saved' -> 'update to MS Artificial Intelligence'."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        # Turn 1
        r1 = client.post(
            "/api/memory/copilot-chat",
            json={"message": "what degree is saved"}
        )
        assert r1.status_code == 200

        # Turn 2: User says 'update to MS Artificial Intelligence'
        r2 = client.post(
            "/api/memory/copilot-chat",
            json={
                "message": "update to MS Artificial Intelligence",
                "history": [
                    {"role": "user", "content": "what degree is saved"},
                    {"role": "assistant", "content": r1.json()["data"]["reply"]}
                ]
            }
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["data"]["intent"] == "UPDATE"
        assert any(u["key"] == "degree" for u in data2["data"]["updates"])

        db_session.expire_all()
        p_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
        assert p_info.degree == "MS Artificial Intelligence"


def test_copilot_multi_turn_custom_field_update_local(client: TestClient, db_session: Session, seed_user_data):
    """Verify saving custom field, querying it, and contextual follow-up update."""
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        # Turn 1: Save custom field
        r1 = client.post(
            "/api/memory/copilot-chat",
            json={"message": "my favroite fruit is mango"}
        )
        assert r1.status_code == 200
        assert r1.json()["data"]["intent"] == "UPDATE"

        # Turn 2: Query it
        r2 = client.post(
            "/api/memory/copilot-chat",
            json={"message": "what is my favorite fruit"}
        )
        assert r2.status_code == 200
        assert "mango" in r2.json()["data"]["reply"]

        # Turn 3: Follow-up contextual update
        r3 = client.post(
            "/api/memory/copilot-chat",
            json={
                "message": "change to peach",
                "history": [
                    {"role": "user", "content": "what is my favorite fruit"},
                    {"role": "assistant", "content": r2.json()["data"]["reply"]}
                ]
            }
        )
        assert r3.status_code == 200
        assert r3.json()["data"]["intent"] == "UPDATE"

        db_session.expire_all()
        cf = db_session.query(CustomField).filter(CustomField.user_id == 1, CustomField.field_key == "favorite_fruit").first()
        assert cf is not None
        assert cf.field_value == "peach"


def test_copilot_multi_turn_name_update_with_conversational_prefix_and_typo_local(client: TestClient, db_session: Session, seed_user_data):
    """
    Verify exact user scenario:
    Turn 1: 'WHAT IS MY CURRENTLY SAVED NAME IS' -> returns legal name
    Turn 2: 'OK CHNAGE IT TO TAHA ALI' -> resolves 'IT' to full_name, updates DB, confirms update.
    """
    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        # Turn 1
        r1 = client.post(
            "/api/memory/copilot-chat",
            json={"message": "WHAT IS MY CURRENTLY SAVED NAME IS"}
        )
        assert r1.status_code == 200
        reply1 = r1.json()["data"]["reply"]
        assert "Muazam Ali" in reply1

        # Turn 2: 'OK CHNAGE IT TO TAHA ALI' with history
        r2 = client.post(
            "/api/memory/copilot-chat",
            json={
                "message": "OK CHNAGE IT TO TAHA ALI",
                "history": [
                    {"role": "user", "content": "WHAT IS MY CURRENTLY SAVED NAME IS"},
                    {"role": "assistant", "content": reply1}
                ]
            }
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["success"] is True
        assert data2["data"]["intent"] == "UPDATE"
        assert len(data2["data"]["updates"]) > 0
        upd = data2["data"]["updates"][0]
        assert upd["key"] == "full_name"
        assert "Taha Ali" in upd["new_value"]

        # Verify DB persistence
        db_session.expire_all()
        user = db_session.query(User).filter(User.id == 1).first()
        p_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
        assert user.full_name == "Taha Ali"
        assert p_info.full_name == "Taha Ali"


def test_delete_personal_info_field_endpoint(client: TestClient, db_session: Session, seed_user_data):
    """Verify deleting/clearing an individual personal_info field via DELETE endpoint."""
    r = client.delete("/api/users/1/personal-info/fields/phone")
    assert r.status_code == 200
    assert r.json()["success"] is True

    db_session.expire_all()
    p_info = db_session.query(PersonalInfo).filter(PersonalInfo.user_id == 1).first()
    assert p_info.phone is None


def test_copilot_conversational_thanks_acknowledgment_with_laptop_custom_field(client: TestClient, db_session: Session, seed_user_data):
    """
    Verify exact user bug:
    When user has custom field 'Do You Have Your Own Laptop And Stable Internet Connect?' = 'No',
    saying 'OK THANK YOU' or 'thank you' must return a polite acknowledgment and MUST NOT
    hallucinate or dump the laptop/internet field!
    """
    cf = CustomField(
        user_id=1,
        field_key="do_you_have_laptop_internet",
        field_label="Do You Have Your Own Laptop And Stable Internet Connect?",
        field_value="No",
        category="personal"
    )
    db_session.add(cf)
    db_session.commit()

    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        # User says 'OK THANK YOU'
        r = client.post(
            "/api/memory/copilot-chat",
            json={"message": "OK THANK YOU"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        reply = data["data"]["reply"]

        # MUST NOT dump the laptop question
        assert "Laptop" not in reply
        assert "Internet" not in reply
        assert "No" not in reply.split()

        # MUST be a warm courtesy acknowledgment
        assert "welcome" in reply.lower()
        assert len(data["data"]["updates"]) == 0


def test_copilot_query_laptop_custom_field_substantive(client: TestClient, db_session: Session, seed_user_data):
    """
    Verify that when user substantively asks about their laptop/internet,
    the custom field is correctly retrieved.
    """
    cf = CustomField(
        user_id=1,
        field_key="do_you_have_laptop_internet",
        field_label="Do You Have Your Own Laptop And Stable Internet Connect?",
        field_value="No",
        category="personal"
    )
    db_session.add(cf)
    db_session.commit()

    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        r = client.post(
            "/api/memory/copilot-chat",
            json={"message": "do I have a laptop or stable internet saved?"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        reply = data["data"]["reply"]
        assert "Do You Have Your Own Laptop And Stable Internet Connect?" in reply
        assert "No" in reply


def test_copilot_user_reported_full_session_flow(client: TestClient, db_session: Session, seed_user_data):
    """
    Verify complete flow from user prompt:
    1. 'WHAT IS MY CURRENT NAMED IS SAVED' -> reports saved name 'Muazam Ali'
    2. 'CHNAGE IT TO TAHA ALI' -> updates legal name to 'Taha Ali'
    3. 'OK THANK YOU' -> says 'You're very welcome!', does NOT hallucinate laptop!
    """
    cf = CustomField(
        user_id=1,
        field_key="do_you_have_laptop_internet",
        field_label="Do You Have Your Own Laptop And Stable Internet Connect?",
        field_value="No",
        category="personal"
    )
    db_session.add(cf)
    db_session.commit()

    with patch("app.ai.provider_manager.AIProviderManager.query_llm", new=AsyncMock(return_value=None)):
        # Turn 1
        r1 = client.post(
            "/api/memory/copilot-chat",
            json={"message": "WHAT IS MY CURRENT NAMED IS SAVED"}
        )
        assert r1.status_code == 200
        reply1 = r1.json()["data"]["reply"]
        assert "Muazam Ali" in reply1

        # Turn 2
        r2 = client.post(
            "/api/memory/copilot-chat",
            json={
                "message": "CHNAGE IT TO TAHA ALI",
                "history": [
                    {"role": "user", "content": "WHAT IS MY CURRENT NAMED IS SAVED"},
                    {"role": "assistant", "content": reply1}
                ]
            }
        )
        assert r2.status_code == 200
        data2 = r2.json()["data"]
        assert data2["intent"] == "UPDATE"
        assert any(u["new_value"] == "Taha Ali" for u in data2["updates"])
        reply2 = data2["reply"]

        # Turn 3
        r3 = client.post(
            "/api/memory/copilot-chat",
            json={
                "message": "OK THANK YOU",
                "history": [
                    {"role": "user", "content": "WHAT IS MY CURRENT NAMED IS SAVED"},
                    {"role": "assistant", "content": reply1},
                    {"role": "user", "content": "CHNAGE IT TO TAHA ALI"},
                    {"role": "assistant", "content": reply2}
                ]
            }
        )
        assert r3.status_code == 200
        data3 = r3.json()["data"]
        assert data3["intent"] == "QUERY"
        assert len(data3["updates"]) == 0
        reply3 = data3["reply"]
        assert "welcome" in reply3.lower()
        assert "laptop" not in reply3.lower()
        assert "internet" not in reply3.lower()




