import pytest
from fastapi.testclient import TestClient
from app.services.extraction_service import (
    extract_structured_memory_from_text,
    save_extracted_memory_to_database,
    _fallback_heuristic_extraction,
)
from app.services.matching_service import match_form_fields
from app.schemas.matching import FieldMatchRequest, DetectedField
from app.database.models import User, PersonalInfo, CustomField


def test_custom_field_crud_endpoints(client: TestClient, db_session):
    """Test manual REST CRUD operations on custom fields."""
    # 1. Create a user
    user_res = client.post("/api/users", json={})
    user_id = user_res.json()["data"]["id"]

    # 2. Add custom field
    create_res = client.post(
        f"/api/users/{user_id}/custom-fields",
        json={
            "field_key": "friends_name",
            "field_label": "Friend's Name",
            "field_value": "Taha",
            "category": "contact"
        }
    )
    assert create_res.status_code == 201
    cf_data = create_res.json()["data"]
    field_id = cf_data["id"]
    assert cf_data["field_key"] == "friends_name"
    assert cf_data["field_value"] == "Taha"

    # 3. List custom fields
    list_res = client.get(f"/api/users/{user_id}/custom-fields")
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 1

    # 4. Update custom field
    update_res = client.put(
        f"/api/custom-fields/{field_id}",
        json={
            "field_value": "Usman"
        }
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["field_value"] == "Usman"

    # 5. Delete custom field
    del_res = client.delete(f"/api/custom-fields/{field_id}")
    assert del_res.status_code == 200

    # Verify deleted
    list_after_res = client.get(f"/api/users/{user_id}/custom-fields")
    assert len(list_after_res.json()["data"]) == 0


def test_friend_name_does_not_overwrite_user_name(client: TestClient, db_session):
    """
    Critical regression test:
    When user inputs 'Friends Name is Taha', it must create a custom field
    and NEVER overwrite the primary user's full_name.
    """
    # 1. Create user with an actual personal name
    user = User(id=101)
    db_session.add(user)
    db_session.commit()

    personal_info = PersonalInfo(
        user_id=101,
        full_name="Muazam Ali",
        email="muazam@example.com"
    )
    db_session.add(personal_info)
    db_session.commit()

    # 2. Ingest raw text 'Friends Name is Taha'
    extracted = {
        "personal_info": None,
        "experiences": [],
        "custom_fields": [
            {
                "field_key": "friends_name",
                "field_label": "Friend's Name",
                "field_value": "Taha",
                "category": "contact"
            }
        ]
    }

    profile = save_extracted_memory_to_database(db=db_session, user_id=101, extracted_data=extracted)

    # 3. Assert full_name is preserved as 'Muazam Ali'
    assert profile["personal_info"].full_name == "Muazam Ali"
    assert len(profile["custom_fields"]) == 1
    assert profile["custom_fields"][0].field_key == "friends_name"
    assert profile["custom_fields"][0].field_value == "Taha"

    # 4. Now user updates friend name: 'Friends Name is Usman'
    extracted_update = {
        "personal_info": None,
        "experiences": [],
        "custom_fields": [
            {
                "field_key": "friends_name",
                "field_label": "Friend's Name",
                "field_value": "Usman",
                "category": "contact"
            }
        ]
    }
    profile_updated = save_extracted_memory_to_database(db=db_session, user_id=101, extracted_data=extracted_update)

    # Assert no duplicate field was created; value updated in place
    assert profile_updated["personal_info"].full_name == "Muazam Ali"
    assert len(profile_updated["custom_fields"]) == 1
    assert profile_updated["custom_fields"][0].field_value == "Usman"


def test_repeated_mail_updates_in_place(client: TestClient, db_session):
    """
    Test that when user repeatedly inputs personal mail or updates it,
    it updates the record rather than duplicating or corrupting other fields.
    """
    user = User(id=202)
    db_session.add(user)
    db_session.commit()

    # 1. First mail ingestion
    data1 = {
        "personal_info": {"email": "oldmail@example.com"},
        "experiences": [],
        "custom_fields": [
            {
                "field_key": "personal_mail",
                "field_label": "Personal Mail",
                "field_value": "oldmail@example.com",
                "category": "email"
            }
        ]
    }
    profile1 = save_extracted_memory_to_database(db=db_session, user_id=202, extracted_data=data1)
    assert len(profile1["custom_fields"]) == 1
    assert profile1["custom_fields"][0].field_value == "oldmail@example.com"

    # 2. Second mail update
    data2 = {
        "personal_info": {"email": "newmail@example.com"},
        "experiences": [],
        "custom_fields": [
            {
                "field_key": "personal_mail",
                "field_label": "Personal Mail",
                "field_value": "newmail@example.com",
                "category": "email"
            }
        ]
    }
    profile2 = save_extracted_memory_to_database(db=db_session, user_id=202, extracted_data=data2)
    # Still only 1 custom field, updated to new value
    assert len(profile2["custom_fields"]) == 1
    assert profile2["custom_fields"][0].field_value == "newmail@example.com"


@pytest.mark.anyio
async def test_form_matching_with_custom_field(client: TestClient, db_session):
    """
    Verify that when a form field asks for 'Friend's Name',
    the matching service matches it to the stored custom field.
    """
    user = User(id=303)
    db_session.add(user)
    db_session.commit()

    cf = CustomField(
        user_id=303,
        field_key="friends_name",
        field_label="Friend's Name",
        field_value="Taha",
        category="contact"
    )
    db_session.add(cf)
    db_session.commit()

    req = FieldMatchRequest(
        user_id=303,
        fields=[
            DetectedField(
                field_id="friend_input",
                name="friends_name",
                label="Friend's Name",
                placeholder="Enter friend's name",
                input_type="text"
            )
        ]
    )

    result = await match_form_fields(db=db_session, request=req)
    assert result.total_mapped == 1
    mapping = result.mappings[0]
    assert mapping.field_id == "friend_input"
    assert mapping.value == "Taha"
    assert mapping.memory_key == "custom_fields.friends_name"


def test_heuristic_fallback_recognizes_friend_name():
    """Verify that regex fallback correctly separates Friend's Name from full_name."""
    res = _fallback_heuristic_extraction("Friends Name is Taha")
    assert res["personal_info"] is None
    assert len(res["custom_fields"]) == 1
    assert res["custom_fields"][0]["field_key"] == "friends_name"
    assert res["custom_fields"][0]["field_value"] == "Taha"
