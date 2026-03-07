import os
from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    print("Engine:", engine.url)
    try:    
        conn.execute(text("ALTER TABLE listings ADD COLUMN location VARCHAR;"))
        print("Added location to listings")
    except Exception as e:
        print("listing alter error:", e)
    
    conn.commit()

print("Migration done")
