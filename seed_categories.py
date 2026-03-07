import json
from app.db.session import SessionLocal, engine
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
        "subcategories": ["Mobile phone", "Accessories", "Tablets"],
        "filter_config": [
            {"key": "brand", "label": "Brand", "type": "select", "options": ["Apple", "Samsung", "Google", "OnePlus", "Xiaomi"]},
            {"key": "storage", "label": "Storage", "type": "select", "options": ["64GB", "128GB", "256GB", "512GB"]}
        ]
    },
    {
        "name": "Electronics",
        "description": "TVs, Laptops, Cameras",
        "icon": "kitchen",
        "subcategories": ["TV", "Laptop", "Camera", "Home Appliance"],
        "filter_config": []
    },
    {
        "name": "Vehicles",
        "description": "Cars and bikes",
        "icon": "directions_car",
        "subcategories": ["Car", "Bike", "Commercial Vehicle"],
        "filter_config": [
            {"key": "brand", "label": "Brand", "type": "select", "options": ["Tesla", "Toyota", "Honda", "BMW", "Mercedes", "Ford"]},
            {"key": "fuel_type", "label": "Fuel Type", "type": "select", "options": ["Petrol", "Diesel", "Electric", "Hybrid"]},
            {"key": "transmission", "label": "Transmission", "type": "select", "options": ["Automatic", "Manual"]}
        ]
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
            subcategories=cat["subcategories"],
            filter_config=cat.get("filter_config", [])
        )
        db.add(c)
    db.commit()
    print("Categories seeded in", db.get_bind().url)
except Exception as e:
    print("Seed error:", e)
    db.rollback()
finally:
    db.close()
