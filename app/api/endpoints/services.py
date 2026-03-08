from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from ...db.session import get_db
from ...models.user import User
from ...models.services import ServiceCategory, ServiceProfile, ServiceBooking
from ...api.deps import get_current_user

router = APIRouter()

from ...schemas.services import ServiceCategoryRead, ServiceProfileRead, ServiceBookingCreate, ServiceBookingRead

# --- Endpoints ---

@router.get("/categories", response_model=List[ServiceCategoryRead])
def get_service_categories(db: Session = Depends(get_db)):
    """Get all active service categories."""
    categories = db.query(ServiceCategory).filter(ServiceCategory.active_status == True).all()
    # Seed default categories if empty
    if not categories:
        default_cats = [
            {"name": "Housemaid", "icon": "cleaning_services", "description": "Professional house cleaning"},
            {"name": "Cook/Chef", "icon": "soup_kitchen", "description": "Home cooked meals and catering"},
            {"name": "Plumber", "icon": "plumbing", "description": "Pipe repairs and installation"},
            {"name": "Electrician", "icon": "electrical_services", "description": "Wiring and electrical repairs"},
        ]
        for c in default_cats:
            db.add(ServiceCategory(**c))
        db.commit()
        categories = db.query(ServiceCategory).filter(ServiceCategory.active_status == True).all()
        
    return categories


@router.get("/search", response_model=List[ServiceProfileRead])
def search_services(
    category_id: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Search for service providers."""
    query = db.query(ServiceProfile).filter(ServiceProfile.active_status == True)
    
    if category_id:
        query = query.filter(ServiceProfile.category_id == category_id)
    if location:
        # Basic exact match for now, could be enhanced with geospatial search later
        query = query.filter(ServiceProfile.location.ilike(f"%{location}%"))
        
    return query.all()


@router.post("/book", response_model=ServiceBookingRead)
def create_booking(
    booking_in: ServiceBookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new service booking request."""
    profile = db.query(ServiceProfile).filter(ServiceProfile.id == booking_in.service_profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Service profile not found")
        
    if profile.provider_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot book your own service")
        
    booking = ServiceBooking(
        customer_id=current_user.id,
        service_profile_id=profile.id,
        provider_id=profile.provider_id,
        scheduled_date=booking_in.scheduled_date,
        service_address=booking_in.service_address,
        instructions=booking_in.instructions,
        quoted_price=profile.base_price,
        price_type=profile.price_type,
        status="pending"
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/bookings/me", response_model=List[ServiceBookingRead])
def get_my_bookings(
    # type: 'customer' or 'provider'
    role: str = "customer", 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bookings where current user is customer or provider."""
    if role == "customer":
        return db.query(ServiceBooking).filter(ServiceBooking.customer_id == current_user.id).order_by(ServiceBooking.created_at.desc()).all()
    elif role == "provider":
        return db.query(ServiceBooking).filter(ServiceBooking.provider_id == current_user.id).order_by(ServiceBooking.created_at.desc()).all()
    else:
        raise HTTPException(status_code=400, detail="Invalid role specified")
