"""
Database Migration Script: Add Google OAuth columns to PostgreSQL users table.

Adds:
  - google_id (VARCHAR(255), UNIQUE, INDEXED)
  - auth_provider (VARCHAR(50), DEFAULT 'local')
  - avatar_url (VARCHAR(1024), NULLABLE)
  - full_name (VARCHAR(255), NULLABLE)

Safe and idempotent: uses ADD COLUMN IF NOT EXISTS and CREATE UNIQUE INDEX IF NOT EXISTS.
"""
import sys
import os

# Add parent directory to sys.path so app modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.database import engine, settings


def run_migration():
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1]}")
    with engine.connect() as conn:
        print("Checking and applying schema migration on 'users' table...")
        
        # Add google_id and unique index
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)"))
        print("[OK] google_id column and unique index verified.")
        
        # Add auth_provider
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50) DEFAULT 'local'"))
        print("[OK] auth_provider column verified.")
        
        # Add avatar_url
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(1024)"))
        print("[OK] avatar_url column verified.")
        
        # Add full_name
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255)"))
        print("[OK] full_name column verified.")

        
        conn.commit()
        print("Migration applied successfully!")


if __name__ == "__main__":
    run_migration()
