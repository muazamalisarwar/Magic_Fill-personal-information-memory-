"""
Live PostgreSQL Verification Script for Magic Fill
--------------------------------------------------
Validates:
1. Real PostgreSQL 18 connection using psycopg 3.
2. Migrated record integrity for user 1 (Muazam Ali).
3. Primary key autoincrement sequence functionality.
4. FastAPI app startup and response with PostgreSQL active.
"""

import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy import text
from app.database.database import engine, SessionLocal, settings
from app.database.models import User, PersonalInfo, Experience, CustomField, UserDocument
from app.main import app

def verify():
    print("=" * 60)
    print("LIVE POSTGRESQL VERIFICATION")
    print("=" * 60)
    print(f"Engine URL: {engine.url}")
    print(f"Dialect: {engine.dialect.name} (Driver: {engine.dialect.driver})")
    
    assert engine.dialect.name == "postgresql", f"Expected postgresql, got {engine.dialect.name}"
    assert "psycopg" in engine.dialect.driver, f"Expected psycopg driver, got {engine.dialect.driver}"

    # 1. Direct DB queries
    db = SessionLocal()
    try:
        # Check user 1
        user1 = db.query(User).filter_by(id=1).first()
        assert user1 is not None, "User 1 not found in PostgreSQL!"
        print(f"[OK] Found User id={user1.id}, created_at={user1.created_at}")

        # Check personal_info
        pi = db.query(PersonalInfo).filter_by(user_id=1).first()
        assert pi is not None, "PersonalInfo for user 1 not found in PostgreSQL!"
        print(f"[OK] Found PersonalInfo for: '{pi.full_name}', CNIC: {pi.cnic}, DOB: {pi.date_of_birth}, City: {pi.city}")
        assert pi.full_name == "MUAZAM ALI", f"Unexpected name: {pi.full_name}"

        # Check experiences
        exps = db.query(Experience).filter_by(user_id=1).all()
        print(f"[OK] Found {len(exps)} Experiences:")
        for e in exps:
            print(f"   - {e.job_title} at {e.company} ({e.start_date} to {e.end_date or 'Present'})")
        assert len(exps) == 3, f"Expected 3 experiences, found {len(exps)}"

        # Check custom fields
        cfs = db.query(CustomField).filter_by(user_id=1).all()
        print(f"[OK] Found {len(cfs)} Custom Fields:")
        for cf in cfs:
            print(f"   - {cf.field_label} ({cf.field_key}) = '{cf.field_value}'")
        assert len(cfs) == 8, f"Expected 8 custom fields, found {len(cfs)}"

        # 2. Test Autoincrement Sequence (create temporary test user & rollback/delete)
        print("\nTesting PostgreSQL Sequence & Autoincrement Insertion...")
        test_user = User()
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        test_user_id = test_user.id
        print(f"[OK] Inserted new User with generated id={test_user_id} (Sequence working cleanly!)")
        assert test_user_id > 1, f"Expected generated id > 1, got {test_user_id}"

        # Insert experience for test user
        test_exp = Experience(
            user_id=test_user_id,
            company="Test Corp",
            job_title="QA Engineer",
            start_date="2025-01-01"
        )
        db.add(test_exp)
        db.commit()
        db.refresh(test_exp)
        print(f"[OK] Inserted Experience with generated id={test_exp.id}")

        # Clean up test user (CASCADE test)
        db.delete(test_user)
        db.commit()
        exp_still_exists = db.query(Experience).filter_by(id=test_exp.id).first()
        assert exp_still_exists is None, "Foreign key CASCADE delete failed!"
        print("[OK] CASCADE deletion verified successfully.")

    finally:
        db.close()

    # 3. Test API via TestClient using actual PostgreSQL engine (no override)
    print("\nTesting FastAPI HTTP endpoints against live PostgreSQL...")
    with TestClient(app) as client:
        # Health check
        res = client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print(f"[OK] GET /health: {res.json()}")

        # Current memory endpoint
        res = client.get("/api/memory/current?user_id=1")
        assert res.status_code == 200, f"Memory endpoint failed: {res.text}"
        data = res.json()["data"]
        print(f"[OK] GET /api/memory/current?user_id=1: Name='{data['personal_info']['full_name']}', Exps={len(data['experiences'])}, CustomFields={len(data['custom_fields'])}")
        assert data["personal_info"]["full_name"] == "MUAZAM ALI"

        # Matching endpoint (used by Chrome Extension autofill)
        match_payload = {
            "user_id": 1,
            "fields": [
                {"field_id": "f_name", "name": "full_name", "label": "Full Name", "input_type": "text"},
                {"field_id": "f_cnic", "name": "applicant_cnic", "label": "National ID / CNIC", "input_type": "text"},
                {"field_id": "f_company", "name": "company", "label": "Current Organization", "input_type": "text"}
            ]
        }
        res = client.post("/api/matching/fields", json=match_payload)
        assert res.status_code == 200, f"Matching endpoint failed: {res.text}"
        data = res.json()["data"]
        mappings = data["mappings"]
        print(f"[OK] POST /api/matching/fields (Browser Extension autofill): mapped {len(mappings)} fields")
        for m in mappings:
            print(f"   - {m['field_id']} -> '{m['value']}' (Confidence: {m['confidence']})")

    print("\n" + "=" * 60)
    print("ALL LIVE POSTGRESQL VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    verify()
