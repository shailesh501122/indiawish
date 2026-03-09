from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional, Any, Dict
from ...db.session import get_db
from ...models.marketplace import Listing, Category, Property, SubCategory, ListingInteraction
from ...schemas.marketplace import ListingRead, ListingCreate, CategoryRead, PropertyRead, PropertyCreate, GlobalSearchItem
from ...models.services import ServiceProfile, ServiceCategory
from sqlalchemy import desc, or_, func
from datetime import datetime, timedelta

router = APIRouter()

# Helper to get sio instance from app
def get_sio():
    from ..main import app
    return app.sio

@router.get("/categories", response_model=List[CategoryRead])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).options(selectinload(Category.subcategory_list)).filter(Category.active_status == True).all()

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

@router.get("/home/trending", response_model=List[ListingRead])
def get_trending_listings(db: Session = Depends(get_db)):
    # Get listings with most interactions in the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    trending_ids = db.query(
        ListingInteraction.listing_id,
        func.count(ListingInteraction.id).label('interaction_count')
    ).filter(
        ListingInteraction.created_at >= seven_days_ago
    ).group_by(
        ListingInteraction.listing_id
    ).order_by(
        desc('interaction_count')
    ).limit(10).all()
    
    if not trending_ids:
        # Fallback to fresh listings if no recent interactions
        return db.query(Listing).filter(
            Listing.status == "Active", 
            Listing.active_status == True
        ).order_by(desc(Listing.created_at)).limit(10).all()
        
    ids = [t[0] for t in trending_ids]
    listings = db.query(Listing).filter(Listing.id.in_(ids)).all()
    # Sort listings according to original trending order
    listings.sort(key=lambda x: ids.index(x.id))
    
    return listings


@router.get("/search/global", response_model=List[GlobalSearchItem])
def global_search(
    query: str = Query(..., min_length=2),
    db: Session = Depends(get_db)
):
    """
    Search across Listings, Categories, and Services.
    """
    results = []
    search_term = f"%{query}%"

    # 1. Search Listings
    listings = db.query(Listing).filter(
        Listing.active_status == True,
        or_(
            Listing.title.ilike(search_term),
            Listing.description.ilike(search_term)
        )
    ).limit(10).all()
    
    for l in listings:
        img = l.images[0] if l.images else None
        results.append(GlobalSearchItem(
            id=l.id,
            title=l.title,
            type="listing",
            image_url=img,
            price=l.price,
            location=l.location,
            category_name=l.category_name
        ))

    # 2. Search Categories
    categories = db.query(Category).filter(
        Category.active_status == True,
        Category.name.ilike(search_term)
    ).limit(5).all()
    
    for c in categories:
        results.append(GlobalSearchItem(
            id=c.id,
            title=c.name,
            type="category",
            image_url=c.icon,
            category_name="Marketplace"
        ))

    # 3. Search Service Profiles
    services = db.query(ServiceProfile).filter(
        ServiceProfile.active_status == True,
        or_(
            ServiceProfile.title.ilike(search_term),
            ServiceProfile.description.ilike(search_term)
        )
    ).limit(10).all()
    
    for s in services:
        img = s.images[0] if s.images else None
        results.append(GlobalSearchItem(
            id=s.id,
            title=s.title,
            type="service",
            image_url=img,
            price=s.base_price,
            location=s.location,
            category_name="Home Service"
        ))

    return results

# ── Generic routes LAST (so they don't swallow /my, /home/fresh, etc.) ──

# \u2500\u2500\u2500 Feature: AI Price Suggestion \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
from pydantic import BaseModel as PydanticBaseModel

class PriceSuggestRequest(PydanticBaseModel):
    category_id: str
    subcategory_id: Optional[str] = None
    location: Optional[str] = None

@router.post("/price-suggest")
def suggest_price(
    req: PriceSuggestRequest,
    db: Session = Depends(get_db)
):
    """Returns a price range for a listing based on similar active listings."""
    query = db.query(Listing).filter(
        Listing.status == "Active",
        Listing.active_status == True,
        Listing.category_id == req.category_id
    )
    if req.subcategory_id:
        query = query.filter(Listing.subcategory_id == req.subcategory_id)
    
    prices = [l.price for l in query.all() if l.price and l.price > 0]
    
    if not prices:
        return {"message": "Not enough data", "min_price": 0, "max_price": 0, "recommended_price": 0, "similar_count": 0}
    
    prices.sort()
    # Remove outliers: use 10th and 90th percentile
    lo = int(len(prices) * 0.10)
    hi = int(len(prices) * 0.90) + 1
    trimmed = prices[lo:hi] if len(prices) > 5 else prices
    
    min_price = int(min(trimmed))
    max_price = int(max(trimmed))
    recommended = int(sum(trimmed) / len(trimmed))
    
    return {
        "min_price": min_price,
        "max_price": max_price,
        "recommended_price": recommended,
        "similar_count": len(prices)
    }

@router.get("", response_model=List[ListingRead])
def get_listings(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    category_id: Optional[str] = None,
    subcategory_id: Optional[str] = None,
    listing_type: Optional[str] = None,
    has_video: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    query = db.query(Listing).filter(Listing.status == "Active", Listing.active_status == True)
    
    if category_id:
        query = query.filter(Listing.category_id == category_id)
    
    if subcategory_id:
        query = query.filter(Listing.subcategory_id == subcategory_id)

    if listing_type:
        query = query.filter(Listing.listing_type == listing_type)

    if has_video:
        query = query.filter(Listing.video_url != None)
        
    # Dynamic property filtering
    params = request.query_params
    for key, value in params.items():
        if key not in ["category_id", "subcategory_id", "listing_type", "has_video", "skip", "limit"]:
            query = query.filter(Listing.properties[key].astext == value)
            
    listings = query.order_by(desc(Listing.created_at)).offset(skip).limit(limit).all()
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
