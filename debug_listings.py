"""Quick script to debug the ResponseValidationError on ListingRead."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.models.marketplace import Listing
from app.schemas.marketplace import ListingRead

db = SessionLocal()
listings = db.query(Listing).limit(2).all()

for listing in listings:
    print("=" * 60)
    print("Listing ID:", listing.id)
    print("  title:         ", repr(listing.title))
    desc_val = repr(listing.description)
    print("  description:   ", desc_val[:80])
    print("  price:         ", repr(listing.price), "type=", type(listing.price).__name__)
    print("  category_id:   ", repr(listing.category_id), "type=", type(listing.category_id).__name__)
    print("  subcategory:   ", repr(listing.subcategory))
    print("  subcategory_id:", repr(listing.subcategory_id))
    print("  location:      ", repr(listing.location))
    print("  images:        ", repr(listing.images), "type=", type(listing.images).__name__)
    print("  status:        ", repr(listing.status))
    print("  user_id:       ", repr(listing.user_id))
    print("  active_status: ", repr(listing.active_status))
    print("  category_name: ", repr(listing.category_name))
    print("  created_at:    ", repr(listing.created_at))
    print("  updated_at:    ", repr(listing.updated_at))
    print("  owner:         ", repr(listing.owner))
    print("  category:      ", repr(listing.category))
    
    # Try to serialize
    try:
        read = ListingRead.model_validate(listing)
        print("  OK: Serialized successfully")
    except Exception as e:
        print("  VALIDATION ERROR:", e)

db.close()
