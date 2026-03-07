from app.db.session import SessionLocal
from app.models.marketplace import Listing, Property, Category

db = SessionLocal()
try:
    listings = db.query(Listing).all()
    print(f"Total Listings: {len(listings)}")
    for l in listings:
        print(f"ID: {l.id}, Title: {l.title}, Status: {l.status}, ActiveStatus: {getattr(l, 'active_status', 'N/A')}")
    
    active_listings = db.query(Listing).filter(Listing.status == "Active", Listing.active_status == True).all()
    print(f"Active Listings: {len(active_listings)}")
    
    categories = db.query(Category).all()
    print(f"Total Categories: {len(categories)}")
    
    properties = db.query(Property).all()
    print(f"Total Properties: {len(properties)}")
finally:
    db.close()
