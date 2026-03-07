import os
from sqlalchemy import text
from app.db.session import engine, Base
from app.models.marketplace import Category, Listing

# Ensure tables exist
Base.metadata.create_all(bind=engine)

with engine.connect() as conn:
    print("Engine:", engine.url)
    try:
        conn.execute(text("ALTER TABLE categories ADD COLUMN subcategories JSON;"))
        print("Added subcategories to categories")
    except Exception as e:
        print("category alter error:", e)
        
    try:    
        conn.execute(text("ALTER TABLE listings ADD COLUMN subcategory VARCHAR;"))
        print("Added subcategory to listings")
    except Exception as e:
        print("listing alter error:", e)
    
    conn.commit()

print("Migration done")
