import os
from sqlalchemy import text
from app.db.session import engine

def fix_users_schema():
    print(f"Connecting to: {engine.url}")
    with engine.connect() as conn:
        # Check existing columns
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
        columns = [row[0] for row in result]
        print(f"Existing columns in 'users': {columns}")

        # Add verification_level
        if 'verification_level' not in columns:
            print("Adding 'verification_level' column...")
            try:
                # First try to create the enum type (it might already exist)
                conn.execute(text("CREATE TYPE verification_level_enum AS ENUM ('unverified', 'phone', 'id', 'top_seller');"))
                print("Created 'verification_level_enum' type.")
            except Exception as e:
                print(f"Note: Enum type might already exist: {e}")
                conn.execute(text("ROLLBACK")) # Rollback the sub-transaction if needed

            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN verification_level verification_level_enum DEFAULT 'unverified';"))
                print("Added 'verification_level' column successfully.")
            except Exception as e:
                print(f"Error adding 'verification_level': {e}")
        else:
            print("'verification_level' column already exists.")

        # Add is_elite if missing
        if 'is_elite' not in columns:
            print("Adding 'is_elite' column...")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_elite BOOLEAN DEFAULT FALSE;"))
                print("Added 'is_elite' column successfully.")
            except Exception as e:
                print(f"Error adding 'is_elite': {e}")

        # Add last_seen if missing
        if 'last_seen' not in columns:
            print("Adding 'last_seen' column...")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_seen TIMESTAMP WITH TIME ZONE;"))
                print("Added 'last_seen' column successfully.")
            except Exception as e:
                print(f"Error adding 'last_seen': {e}")

        conn.commit()
    print("Schema fix-up completed.")

if __name__ == "__main__":
    fix_users_schema()
