import sys
import os
import uuid

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal, engine, Base
from app.models.marketplace import Category, Listing
from app.models.user import User

def seed_database():
    db = SessionLocal()
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # 1. Create a Test User if not exists
    test_email = "test@example.com"
    user = db.query(User).filter(User.email == test_email).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=test_email,
            # Standard bcrypt hash for "password123"
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6L6sL8t62tVf/V1.", 
            first_name="Test",
            last_name="User",
            roles="User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created test user: {test_email}")

    # 2. Categories
    categories_data = [
        {"name": "Cars", "icon": "Car"},
        {"name": "Properties", "icon": "Home"},
        {"name": "Mobile Phones", "icon": "Smartphone"},
        {"name": "Electronics & Appliances", "icon": "Tv"},
        {"name": "Bikes", "icon": "Bike"},
        {"name": "Furniture", "icon": "Sofa"},
    ]
    
    cat_map = {}
    for c_data in categories_data:
        cat = db.query(Category).filter(Category.name == c_data["name"]).first()
        if not cat:
            cat = Category(
                id=str(uuid.uuid4()),
                name=c_data["name"],
                icon=c_data["icon"],
                description=f"All kinds of {c_data['name']}"
            )
            db.add(cat)
            db.commit()
            db.refresh(cat)
        cat_map[c_data["name"]] = cat.id

    # 3. Listings
    listings_data = [
        {
            "title": "Maruti Suzuki Swift 2021 Petrol",
            "price": 550000.0,
            "cat": "Cars",
            "desc": "First owner, well maintained, 15000km driven."
        },
        {
            "title": "2 BHK Flat in Powai, Mumbai",
            "price": 18500000.0,
            "cat": "Properties",
            "desc": "Modern amenities, 10th floor, park facing."
        },
        {
            "title": "iPhone 14 Pro Max - 128GB",
            "price": 85000.0,
            "cat": "Mobile Phones",
            "desc": "Grey color, battery health 92%, with original box."
        },
        {
            "title": "Sony Bravia 55 inch 4K OLED",
            "price": 95000.0,
            "cat": "Electronics & Appliances",
            "desc": "Under warranty, crystal clear display, smart features."
        }
    ]

    for l_data in listings_data:
        # Avoid duplicates by title check
        existing = db.query(Listing).filter(Listing.title == l_data["title"]).first()
        if not existing:
            listing = Listing(
                id=str(uuid.uuid4()),
                title=l_data["title"],
                description=l_data["desc"],
                price=l_data["price"],
                category_id=cat_map[l_data["cat"]],
                user_id=user.id,
                status="Active"
            )
            db.add(listing)
    
    db.commit()
    db.close()
    print("Seeding successful!")

if __name__ == "__main__":
    seed_database()
