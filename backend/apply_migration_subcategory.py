import os
from sqlalchemy import text
from app.db.session import engine, Base
from app.models.marketplace import SubCategory

with engine.connect() as conn:
    print("Engine:", engine.url)
    try:
        # Create subcategories table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS subcategories (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            category_id VARCHAR REFERENCES categories(id),
            active_status BOOLEAN DEFAULT TRUE
        )
        """))
        print("Created subcategories table")
    except Exception as e:
        print("Table create error:", e)
        
    try:    
        conn.execute(text("ALTER TABLE listings ADD COLUMN subcategory_id VARCHAR REFERENCES subcategories(id);"))
        print("Added subcategory_id to listings")
    except Exception as e:
        print("listing alter error:", e)
    
    conn.commit()

print("Migration done")
