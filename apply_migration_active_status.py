import os
from sqlalchemy import text
from app.db.session import engine

tables_to_update = [
    "categories",
    "listings",
    "properties",
    "users",
    "conversations",
    "messages"
]

with engine.connect() as conn:
    print("Engine:", engine.url)
    for table_name in tables_to_update:
        try:
            # We are using PostgreSQL so BOOLEAN default true is valid
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN active_status BOOLEAN DEFAULT TRUE;"))
            print(f"Added active_status to {table_name}")
        except Exception as e:
            # Table might already have the column or table might not exist in local dev
            print(f"Error for {table_name}:", e)
    
    conn.commit()

print("Migration for active_status done")
