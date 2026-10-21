import pytest
from app.services.document_service import classify_document_description


def test_classify_document_descriptions():
    """Test smart classification of natural language descriptions into canonical keys."""
    # CNIC front
    k1, t1, c1 = classify_document_description("this is my cnic front", "image.jpg")
    assert k1 == "cnic_front"
    assert t1 == "CNIC Front"
    assert c1 == "identity"

    # CNIC back
    k2, t2, c2 = classify_document_description("this is my cnic back", "doc.png")
    assert k2 == "cnic_back"
    assert t2 == "CNIC Back"
    assert c2 == "identity"

    # Profile photo
    k3, t3, c3 = classify_document_description("my official profile picture", "pic.jpg")
    assert k3 == "profile_photo"
    assert t3 == "Profile Photograph"
    assert c3 == "profile"

    # Passport
    k4, t4, c4 = classify_document_description("my passport scan", "pass.pdf")
    assert k4 == "passport"
    assert t4 == "Passport Document"

    # Transcript
    k5, t5, c5 = classify_document_description("BS degree transcript certificate", "transcript.pdf")
    assert k5 == "degree_transcript"
    assert c5 == "academic"


def test_create_and_list_documents(client):
    """Test saving documents with descriptions and retrieving them."""
    user_id = client.post("/api/users", json={}).json()["data"]["id"]

    photo_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    cnic_front_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    cnic_back_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP4z8BQDwAEgAGAB0/1lQAAAABJRU5ErkJggg=="

    # 1. Save CNIC Front
    r1 = client.post(
        "/api/documents",
        json={
            "user_id": user_id,
            "description": "this is my cnic front",
            "file_name": "cnic_front.jpg",
            "mime_type": "image/jpeg",
            "file_data": cnic_front_uri
        }
    )
    assert r1.status_code == 201
    d1 = r1.json()["data"]
    assert d1["doc_key"] == "cnic_front"
    assert d1["title"] == "CNIC Front"
    assert d1["description"] == "this is my cnic front"

    # 2. Save CNIC Back
    r2 = client.post(
        "/api/documents",
        json={
            "user_id": user_id,
            "description": "this is my cnic back",
            "file_name": "cnic_back.jpg",
            "mime_type": "image/jpeg",
            "file_data": cnic_back_uri
        }
    )
    assert r2.status_code == 201
    d2 = r2.json()["data"]
    assert d2["doc_key"] == "cnic_back"
    assert d2["title"] == "CNIC Back"

    # 3. Save Profile Photo
    r3 = client.post(
        "/api/documents",
        json={
            "user_id": user_id,
            "description": "my profile picture",
            "file_name": "avatar.png",
            "mime_type": "image/png",
            "file_data": photo_uri
        }
    )
    assert r3.status_code == 201
    d3 = r3.json()["data"]
    assert d3["doc_key"] == "profile_photo"

    # 4. List documents for user
    list_res = client.get(f"/api/documents?user_id={user_id}")
    assert list_res.status_code == 200
    docs = list_res.json()["data"]
    assert len(docs) == 3

    # 5. Verify User Profile includes documents
    profile_res = client.get(f"/api/users/{user_id}/profile")
    assert profile_res.status_code == 200
    prof_docs = profile_res.json()["data"]["documents"]
    assert len(prof_docs) == 3

    # 6. Test Form Matching for CNIC Front, CNIC Back, and Profile Photo
    match_payload = {
        "user_id": user_id,
        "fields": [
            {"field_id": "inp_photo", "label": "Upload Photograph / Headshot", "name": "photo", "input_type": "file"},
            {"field_id": "inp_cnic_front", "label": "Upload CNIC Front Side", "name": "cnic_front", "input_type": "file"},
            {"field_id": "inp_cnic_back", "label": "Upload CNIC Back Side", "name": "cnic_back", "input_type": "file"}
        ]
    }
    match_res = client.post("/api/matching/fields", json=match_payload)
    assert match_res.status_code == 200
    mappings = {m["field_id"]: m for m in match_res.json()["data"]["mappings"]}
    assert mappings["inp_photo"]["value"] == photo_uri
    assert mappings["inp_cnic_front"]["value"] == cnic_front_uri
    assert mappings["inp_cnic_front"]["memory_key"] == "documents.cnic_front"
    assert mappings["inp_cnic_back"]["value"] == cnic_back_uri
    assert mappings["inp_cnic_back"]["memory_key"] == "documents.cnic_back"

    # 7. Delete document
    del_res = client.delete(f"/api/documents/{d1['id']}")
    assert del_res.status_code == 200
    assert len(client.get(f"/api/documents?user_id={user_id}").json()["data"]) == 2
