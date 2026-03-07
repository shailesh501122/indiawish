import os
import sys

# Add backend directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import engine

with engine.connect() as con:
    try:
        print("Adding images column to listings...")
        con.execute(text("ALTER TABLE listings ADD COLUMN IF NOT EXISTS images JSON DEFAULT '[]'::json;"))
        print("Adding images column to properties...")
        con.execute(text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS images JSON DEFAULT '[]'::json;"))
        con.commit()
        print("Successfully added images columns!")
    except Exception as e:
        print(f"Error during migration: {e}")
