from app.db.session import SessionLocal
from app.models.marketplace import Listing
from app.schemas.marketplace import ListingRead
import json

db = SessionLocal()
listings = db.query(Listing).limit(5).all()
print(f"Found {len(listings)} listings")

for l in listings:
    try:
        read = ListingRead.model_validate(l)
        print(f"Listing {l.id} valid")
    except Exception as e:
        print(f"Listing {l.id} INVALID: {e}")
        # Print the data that failed
        data = {c.name: getattr(l, c.name) for c in l.__table__.columns}
        print(f"Data: {data}")
