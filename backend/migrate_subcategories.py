import uuid
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.models.marketplace import Category, SubCategory

db = SessionLocal()

print("Migrating JSON subcategories to table...")
categories = db.query(Category).all()
for cat in categories:
    json_subs = cat.subcategories or []
    for subcat_name in json_subs:
        # Check if exists
        existing = db.query(SubCategory).filter_by(name=subcat_name, category_id=cat.id).first()
        if not existing:
            new_sub = SubCategory(
                id=str(uuid.uuid4()),
                name=subcat_name,
                category_id=cat.id
            )
            db.add(new_sub)
            print(f"Added subcategory '{subcat_name}' to category '{cat.name}'")

db.commit()
db.close()
print("Migration done")
