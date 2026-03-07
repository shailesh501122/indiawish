from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db
from ...models.marketplace import Listing, Category, Property
from ...schemas.marketplace import ListingRead, ListingCreate, CategoryRead, PropertyRead, PropertyCreate
from ...api.deps import get_current_user
from ...models.user import User
from ...models.marketplace import ListingInteraction
from sqlalchemy import desc

router = APIRouter()

# Helper to get sio instance from app
def get_sio():
    from ..main import app
    return app.sio

@router.get("/categories", response_model=List[CategoryRead])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.active_status == True).all()

@router.get("/my", response_model=List[ListingRead])
def get_my_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print(f"DEBUG: Entered get_my_listings for user: {current_user.email} (ID: {current_user.id})")
    listings = db.query(Listing).filter(Listing.user_id == current_user.id).all()
    print(f"DEBUG: Found {len(listings)} personal listings for user {current_user.id}")
    return listings

@router.get("/properties", response_model=List[PropertyRead])
def get_properties(db: Session = Depends(get_db)):
    return db.query(Property).filter(Property.active_status == True).all()

@router.get("/home/fresh", response_model=List[ListingRead])
def get_fresh_recommendations(db: Session = Depends(get_db)):
    # Simple recommendation: Latest active listings
    return db.query(Listing).filter(Listing.status == "Active", Listing.active_status == True).order_by(desc(Listing.created_at)).limit(20).all()

@router.get("/home/recent", response_model=List[ListingRead])
def get_recent_interactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get listings user interacted with (liked or viewed)
    interactions = db.query(ListingInteraction).filter(
        ListingInteraction.user_id == current_user.id
    ).order_by(desc(ListingInteraction.created_at)).limit(10).all()
    
    listing_ids = [i.listing_id for i in interactions]
    # Maintain order of interactions
    listings = []
    for lid in listing_ids:
        l = db.query(Listing).filter(Listing.id == lid, Listing.active_status == True).first()
        if l and l not in listings:
            listings.append(l)
            
    return listings

# ── Generic routes LAST (so they don't swallow /my, /home/fresh, etc.) ──

@router.get("", response_model=List[ListingRead])
def get_listings(
    request: Request,
    category_id: Optional[str] = None,
    subcategory_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    print(f"DEBUG: Entered get_listings (category_id: {category_id}, subcategory_id: {subcategory_id})")
    query = db.query(Listing).filter(Listing.status == "Active", Listing.active_status == True)
    
    if category_id:
        query = query.filter(Listing.category_id == category_id)
    
    if subcategory_id:
        query = query.filter(Listing.subcategory_id == subcategory_id)
        
    # Dynamic property filtering
    # Any query parameter that is not category_id, subcategory_id or request internals is treated as a property filter
    params = request.query_params
    for key, value in params.items():
        if key not in ["category_id", "subcategory_id"]:
            # SQLITE or POSTGRES handle JSON differently but SQLAlchemy abstracts it mostly
            # We assume properties is a JSON/JSONB column
            query = query.filter(Listing.properties[key].astext == value)
            
    listings = query.all()
    print(f"DEBUG: returning {len(listings)} active listings")
    return listings

@router.get("/{listing_id}", response_model=ListingRead)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    listing_obj = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing_obj:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing_obj

@router.post("/{listing_id}/interact")
def track_interaction(
    listing_id: str,
    interaction_type: str, # 'view' or 'like'
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if interaction_type == 'like':
        existing = db.query(ListingInteraction).filter(
            ListingInteraction.user_id == current_user.id,
            ListingInteraction.listing_id == listing_id,
            ListingInteraction.interaction_type == 'like'
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
            return {"status": "unliked"}
            
    interaction = ListingInteraction(
        user_id=current_user.id,
        listing_id=listing_id,
        interaction_type=interaction_type
    )
    db.add(interaction)
    db.commit()
    return {"status": "success"}



@router.post("", response_model=ListingRead)
async def create_listing(
    listing_in: ListingCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_listing = Listing(
        **listing_in.dict(),
        user_id=current_user.id
    )
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    
    # Broadcast new listing to everyone
    try:
        sio = get_sio()
        await sio.emit('new_listing', {
            "id": str(new_listing.id),
            "title": str(new_listing.title),
            "price": float(new_listing.price),
            "image_url": new_listing.images[0] if new_listing.images else None
        })
    except Exception as e:
        print(f"Error broadcasting listing: {e}")
        
    return new_listing



@router.post("/properties", response_model=PropertyRead)
async def create_property(
    property_in: PropertyCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_property = Property(
        **property_in.dict(),
        user_id=current_user.id,
        status="Active"
    )
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
    
    # Broadcast new property to everyone
    try:
        sio = get_sio()
        await sio.emit('new_property', {
            "id": str(new_property.id),
            "title": str(new_property.title),
            "price": float(new_property.price),
            "image_url": new_property.images[0] if new_property.images else None
        })
    except Exception as e:
        print(f"Error broadcasting property: {e}")
        
    return new_property
