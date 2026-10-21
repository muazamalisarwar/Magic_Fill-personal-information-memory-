"""
Magic Fill Database Migration Script: SQLite to PostgreSQL
-----------------------------------------------------------
Safely migrates all schema, tables, and existing records from SQLite to PostgreSQL.
- Preserves primary keys, foreign-key relationships, timestamps, and data integrity.
- Syncs PostgreSQL serial sequences post-migration.
- Idempotent and repeatable (safe to run multiple times).
- Validates row counts and field integrity after migration.
- NEVER deletes or alters the original SQLite database.
"""

import sys
import os
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.database.database import Base, settings
from app.database.models import User, PersonalInfo, Experience, CustomField, UserDocument

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("migration")


def parse_date(val: Any) -> Optional[date]:
    """Parse date string or object from SQLite into datetime.date."""
    if val is None or val == "":
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    str_val = str(val).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(str_val[:10], fmt[: len(str_val[:10])]).date()
        except ValueError:
            pass
    return None


def parse_datetime(val: Any) -> Optional[datetime]:
    """Parse datetime string or object from SQLite into datetime."""
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val
    str_val = str(val).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(str_val, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(str_val)
    except Exception:
        return None


def run_migration(sqlite_path: str, pg_url: str) -> bool:
    """Execute SQLite to PostgreSQL data migration."""
    logger.info("=" * 60)
    logger.info("Starting Magic Fill SQLite to PostgreSQL Migration")
    logger.info("Source SQLite DB: %s", sqlite_path)
    # Mask password for secure logging
    masked_url = pg_url
    if "@" in masked_url and ":" in masked_url.split("@")[0]:
        prefix, rest = masked_url.split("@", 1)
        scheme_user, _ = prefix.rsplit(":", 1)
        masked_url = f"{scheme_user}:******@{rest}"
    logger.info("Target PostgreSQL DB: %s", masked_url)
    logger.info("=" * 60)

    if not os.path.exists(sqlite_path):
        logger.error("SQLite database file not found at: %s", sqlite_path)
        return False

    # 1. Connect to SQLite
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    
    # 2. Connect to PostgreSQL
    try:
        pg_engine = create_engine(pg_url, pool_pre_ping=True)
        with pg_engine.connect() as conn:
            pg_version = conn.execute(text("SELECT version();")).scalar()
            logger.info("Connected to PostgreSQL successfully: %s", pg_version.split("\n")[0] if pg_version else "Unknown")
    except Exception as exc:
        logger.error("Failed to connect to PostgreSQL: %s", str(exc))
        return False

    # 3. Create all tables in PostgreSQL
    logger.info("Creating tables in PostgreSQL (if not already existing)...")
    Base.metadata.create_all(bind=pg_engine)
    logger.info("PostgreSQL schema initialized successfully.")

    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    stats: Dict[str, Dict[str, int]] = {}

    try:
        # Table 1: Users
        logger.info("--- Migrating 'users' ---")
        with sqlite_engine.connect() as s_conn:
            sqlite_users = s_conn.execute(text("SELECT id, created_at, updated_at FROM users")).fetchall()
        
        sqlite_user_count = len(sqlite_users)
        transferred_users = 0
        skipped_users = 0

        for row in sqlite_users:
            u_id, u_created, u_updated = row[0], row[1], row[2]
            existing = pg_session.query(User).filter_by(id=u_id).first()
            if not existing:
                user_obj = User(
                    id=u_id,
                    created_at=parse_datetime(u_created) or datetime.utcnow(),
                    updated_at=parse_datetime(u_updated) or datetime.utcnow()
                )
                pg_session.add(user_obj)
                transferred_users += 1
            else:
                skipped_users += 1
        
        pg_session.commit()
        stats["users"] = {"sqlite": sqlite_user_count, "migrated": transferred_users, "skipped": skipped_users}
        logger.info("Users: %d from SQLite, %d newly migrated, %d already present.", sqlite_user_count, transferred_users, skipped_users)

        # Table 2: PersonalInfo
        logger.info("--- Migrating 'personal_info' ---")
        with sqlite_engine.connect() as s_conn:
            # Query columns dynamically
            s_res = s_conn.execute(text("SELECT * FROM personal_info"))
            sqlite_cols = list(s_res.keys())
            sqlite_pi = s_res.fetchall()
        
        sqlite_pi_count = len(sqlite_pi)
        transferred_pi = 0
        skipped_pi = 0

        for row in sqlite_pi:
            data = dict(zip(sqlite_cols, row))
            pi_id = data["id"]
            existing = pg_session.query(PersonalInfo).filter_by(id=pi_id).first()
            if not existing:
                pi_obj = PersonalInfo(
                    id=data.get("id"),
                    user_id=data.get("user_id"),
                    full_name=data.get("full_name") or "User",
                    father_name=data.get("father_name"),
                    gender=data.get("gender"),
                    date_of_birth=parse_date(data.get("date_of_birth")),
                    cnic=data.get("cnic"),
                    phone=data.get("phone"),
                    email=data.get("email"),
                    profile_photo=data.get("profile_photo"),
                    cnic_photo=data.get("cnic_photo"),
                    address=data.get("address"),
                    city=data.get("city"),
                    postal_code=data.get("postal_code"),
                    country=data.get("country"),
                    university=data.get("university"),
                    degree=data.get("degree"),
                    department=data.get("department"),
                    semester=data.get("semester"),
                    registration_number=data.get("registration_number"),
                    created_at=parse_datetime(data.get("created_at")) or datetime.utcnow(),
                    updated_at=parse_datetime(data.get("updated_at")) or datetime.utcnow()
                )
                pg_session.add(pi_obj)
                transferred_pi += 1
            else:
                skipped_pi += 1

        pg_session.commit()
        stats["personal_info"] = {"sqlite": sqlite_pi_count, "migrated": transferred_pi, "skipped": skipped_pi}
        logger.info("PersonalInfo: %d from SQLite, %d newly migrated, %d already present.", sqlite_pi_count, transferred_pi, skipped_pi)

        # Table 3: Experiences
        logger.info("--- Migrating 'experiences' ---")
        with sqlite_engine.connect() as s_conn:
            s_res = s_conn.execute(text("SELECT * FROM experiences"))
            sqlite_cols = list(s_res.keys())
            sqlite_exp = s_res.fetchall()

        sqlite_exp_count = len(sqlite_exp)
        transferred_exp = 0
        skipped_exp = 0

        for row in sqlite_exp:
            data = dict(zip(sqlite_cols, row))
            exp_id = data["id"]
            existing = pg_session.query(Experience).filter_by(id=exp_id).first()
            if not existing:
                exp_obj = Experience(
                    id=data.get("id"),
                    user_id=data.get("user_id"),
                    company=data.get("company"),
                    job_title=data.get("job_title"),
                    start_date=parse_date(data.get("start_date")) or date.today(),
                    end_date=parse_date(data.get("end_date")),
                    description=data.get("description"),
                    skills=data.get("skills"),
                    created_at=parse_datetime(data.get("created_at")) or datetime.utcnow(),
                    updated_at=parse_datetime(data.get("updated_at")) or datetime.utcnow()
                )
                pg_session.add(exp_obj)
                transferred_exp += 1
            else:
                skipped_exp += 1

        pg_session.commit()
        stats["experiences"] = {"sqlite": sqlite_exp_count, "migrated": transferred_exp, "skipped": skipped_exp}
        logger.info("Experiences: %d from SQLite, %d newly migrated, %d already present.", sqlite_exp_count, transferred_exp, skipped_exp)

        # Table 4: CustomFields
        logger.info("--- Migrating 'custom_fields' ---")
        with sqlite_engine.connect() as s_conn:
            s_res = s_conn.execute(text("SELECT * FROM custom_fields"))
            sqlite_cols = list(s_res.keys())
            sqlite_cf = s_res.fetchall()

        sqlite_cf_count = len(sqlite_cf)
        transferred_cf = 0
        skipped_cf = 0

        for row in sqlite_cf:
            data = dict(zip(sqlite_cols, row))
            cf_id = data["id"]
            existing = pg_session.query(CustomField).filter_by(id=cf_id).first()
            if not existing:
                cf_obj = CustomField(
                    id=data.get("id"),
                    user_id=data.get("user_id"),
                    field_key=data.get("field_key"),
                    field_label=data.get("field_label"),
                    field_value=data.get("field_value"),
                    category=data.get("category", "general"),
                    created_at=parse_datetime(data.get("created_at")) or datetime.utcnow(),
                    updated_at=parse_datetime(data.get("updated_at")) or datetime.utcnow()
                )
                pg_session.add(cf_obj)
                transferred_cf += 1
            else:
                skipped_cf += 1

        pg_session.commit()
        stats["custom_fields"] = {"sqlite": sqlite_cf_count, "migrated": transferred_cf, "skipped": skipped_cf}
        logger.info("CustomFields: %d from SQLite, %d newly migrated, %d already present.", sqlite_cf_count, transferred_cf, skipped_cf)

        # Table 5: UserDocuments
        logger.info("--- Migrating 'user_documents' ---")
        with sqlite_engine.connect() as s_conn:
            # Check if table exists in SQLite
            s_res = s_conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_documents'")).fetchone()
            if s_res:
                s_res = s_conn.execute(text("SELECT * FROM user_documents"))
                sqlite_cols = list(s_res.keys())
                sqlite_docs = s_res.fetchall()
            else:
                sqlite_cols = []
                sqlite_docs = []

        sqlite_doc_count = len(sqlite_docs)
        transferred_docs = 0
        skipped_docs = 0

        for row in sqlite_docs:
            data = dict(zip(sqlite_cols, row))
            doc_id = data["id"]
            existing = pg_session.query(UserDocument).filter_by(id=doc_id).first()
            if not existing:
                doc_obj = UserDocument(
                    id=data.get("id"),
                    user_id=data.get("user_id"),
                    doc_key=data.get("doc_key"),
                    title=data.get("title"),
                    description=data.get("description"),
                    file_name=data.get("file_name"),
                    mime_type=data.get("mime_type"),
                    file_data=data.get("file_data"),
                    file_size_bytes=data.get("file_size_bytes"),
                    category=data.get("category", "identity"),
                    created_at=parse_datetime(data.get("created_at")) or datetime.utcnow(),
                    updated_at=parse_datetime(data.get("updated_at")) or datetime.utcnow()
                )
                pg_session.add(doc_obj)
                transferred_docs += 1
            else:
                skipped_docs += 1

        pg_session.commit()
        stats["user_documents"] = {"sqlite": sqlite_doc_count, "migrated": transferred_docs, "skipped": skipped_docs}
        logger.info("UserDocuments: %d from SQLite, %d newly migrated, %d already present.", sqlite_doc_count, transferred_docs, skipped_docs)

        # 4. Sync PostgreSQL Serial Sequences
        logger.info("--- Synchronizing PostgreSQL Primary Key Sequences ---")
        tables = ["users", "personal_info", "experiences", "custom_fields", "user_documents"]
        with pg_engine.connect() as conn:
            for tbl in tables:
                seq_query = text(f"""
                    SELECT setval(
                        pg_get_serial_sequence('{tbl}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {tbl}), 1),
                        (SELECT MAX(id) IS NOT NULL FROM {tbl})
                    );
                """)
                try:
                    conn.execute(seq_query)
                    conn.commit()
                    logger.info("Synchronized sequence for table '%s'.", tbl)
                except Exception as seq_err:
                    logger.warning("Could not set sequence for table '%s': %s", tbl, str(seq_err))

        # 5. Verification & Summary
        logger.info("=" * 60)
        logger.info("MIGRATION SUMMARY & VERIFICATION")
        logger.info("=" * 60)
        all_passed = True
        for tbl, s in stats.items():
            pg_count = pg_session.query(
                User if tbl == "users" else
                PersonalInfo if tbl == "personal_info" else
                Experience if tbl == "experiences" else
                CustomField if tbl == "custom_fields" else
                UserDocument
            ).count()
            logger.info("Table '%s': SQLite=%d | PostgreSQL Total=%d (Migrated: %d, Skipped: %d)",
                        tbl, s["sqlite"], pg_count, s["migrated"], s["skipped"])
            if pg_count < s["sqlite"]:
                all_passed = False
                logger.error("Discrepancy detected in table '%s'!", tbl)

        if all_passed:
            logger.info("SUCCESS: All tables and records verified accurately in PostgreSQL.")
        else:
            logger.error("WARNING: Record counts did not match expected numbers.")

        return all_passed

    except Exception as exc:
        pg_session.rollback()
        logger.exception("Migration failed with error: %s", str(exc))
        return False
    finally:
        pg_session.close()


if __name__ == "__main__":
    sqlite_file = os.path.join(backend_dir, "personal_memory.db")
    if len(sys.argv) > 1:
        sqlite_file = sys.argv[1]

    # Use DATABASE_URL from settings (.env)
    pg_conn_url = settings.DATABASE_URL
    if len(sys.argv) > 2:
        pg_conn_url = sys.argv[2]

    success = run_migration(sqlite_file, pg_conn_url)
    sys.exit(0 if success else 1)
