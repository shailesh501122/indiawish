import json
from app.db.session import SessionLocal, engine, Base
from app.models.marketplace import Category
import uuid

def generate_uuid():
    return str(uuid.uuid4())

# Categories
categories = [
    {
        "name": "Mobile",
        "description": "Mobile phones and tablets",
        "icon": "smartphone",
        "subcategories": ["Mobile phone", "Accessories", "Tablets"]
    },
    {
        "name": "Electronics",
        "description": "TVs, Laptops, Cameras",
        "icon": "kitchen",
        "subcategories": ["TV", "Laptop", "Camera", "Home Appliance"]
    },
    {
        "name": "Vehicles",
        "description": "Cars and bikes",
        "icon": "directions_car",
        "subcategories": ["Car", "Bike", "Commercial Vehicle"]
    }
]

db = SessionLocal()
try:
    print("Deleting existing categories...")
    db.query(Category).delete()
    
    for cat in categories:
        c = Category(
            id=generate_uuid(),
            name=cat["name"],
            description=cat["description"],
            icon=cat["icon"],
            subcategories=cat["subcategories"]
        )
        db.add(c)
    db.commit()
    print("Categories seeded in", db.get_bind().url)
except Exception as e:
    print("Seed error:", e)
    db.rollback()
finally:
    db.close()
