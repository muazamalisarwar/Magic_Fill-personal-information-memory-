import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.database.database import settings, Base
from app.database.models import User, AuthCode
from app.services.auth_service import hash_password

def migrate():
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1]}")
    engine = create_engine(settings.DATABASE_URL)
    
    # Create all tables (e.g. auth_codes)
    Base.metadata.create_all(bind=engine)
    print("Base.metadata.create_all completed.")

    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
            conn.commit()
            print("PostgreSQL users table updated with auth columns.")

        # Check user 1
        res = conn.execute(text("SELECT id, email, hashed_password FROM users WHERE id = 1;")).fetchone()
        if res:
            u_id, u_email, u_hash = res[0], res[1], res[2]
            if not u_email or not u_hash:
                default_email = "muazam@example.com"
                default_hash = hash_password("MagicFill123!")
                conn.execute(
                    text("UPDATE users SET email = :email, hashed_password = :hash, is_active = TRUE WHERE id = 1;"),
                    {"email": default_email, "hash": default_hash}
                )
                conn.commit()
                print(f"Seeded User #1 credentials: {default_email} / MagicFill123!")
            else:
                print(f"User #1 already has credentials: {u_email}")

    print("Authentication schema migration successful!")

if __name__ == "__main__":
    migrate()
