from app.db.session import SessionLocal
from app.models.marketplace import Category, Listing, Property
from app.models.user import User
from app.core.security import get_password_hash
import uuid

def seed_data():
    db = SessionLocal()
    try:
        # Check if users exist
        if db.query(User).count() == 0:
            print("Seeding users...")
            admin = User(
                id=str(uuid.uuid4()),
                email="admin@indiawish.com",
                hashed_password=get_password_hash("admin123"),
                first_name="Admin",
                last_name="User",
                roles="Admin,User"
            )
            db.add(admin)
            db.commit()
            print("Admin user created.")

        # Seed Categories
        if db.query(Category).count() == 0:
            print("Seeding categories...")
            categories = [
                Category(name="Electronics", description="Phones, Laptops, etc.", icon="devices"),
                Category(name="Fashion", description="Clothes, Shoes, etc.", icon="checkroom"),
                Category(name="Furniture", description="Sofa, Table, etc.", icon="chair"),
                Category(name="Vehicles", description="Cars, Bikes, etc.", icon="directions_car"),
            ]
            db.add_all(categories)
            db.commit()
            print("Categories seeded.")

            # Seed some listings
            cat_electronics = db.query(Category).filter_by(name="Electronics").first()
            admin_user = db.query(User).filter_by(email="admin@indiawish.com").first()
            
            listings = [
                Listing(title="iPhone 15 Pro", description="Silver, 256GB, Brand New", price=120000.0, category_id=cat_electronics.id, user_id=admin_user.id),
                Listing(title="Sony WH-1000XM5", description="Noise cancelling headphones", price=25000.0, category_id=cat_electronics.id, user_id=admin_user.id),
            ]
            db.add_all(listings)
            
            # Seed some properties
            properties = [
                Property(title="Luxury 3BHK Apartment", description="Spacious apartment in city center", price=15000000.0, type="Apartment", city="Delhi", address="Connaught Place", bedrooms=3, bathrooms=3, area=1800.0, user_id=admin_user.id),
                Property(title="Modern Villa with Pool", description="Beautiful villa with a private pool", price=45000000.0, type="Villa", city="Gurgaon", address="Golf Course Road", bedrooms=4, bathrooms=5, area=3500.0, user_id=admin_user.id),
            ]
            db.add_all(properties)
            db.commit()
            print("Listings and Properties seeded.")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
