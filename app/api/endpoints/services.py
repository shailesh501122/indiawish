from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from pydantic import BaseModel

from ...db.session import get_db
from ...models.user import User
from ...models.services import ServiceCategory, ServiceProfile, ServiceBooking
from ...api.deps import get_current_user

router = APIRouter()

from ...schemas.services import (
    ServiceCategoryRead, 
    ServiceProfileRead, 
    ServiceBookingCreate, 
    ServiceBookingRead,
    ServiceLeadCreate,
    ServiceLeadRead,
    LeadAssignmentRead
)

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
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Search for service providers."""
    query = db.query(ServiceProfile).filter(ServiceProfile.active_status == True)
    
    if category_id:
        query = query.filter(ServiceProfile.category_id == category_id)
    if location:
        # Basic exact match for now, could be enhanced with geospatial search later
        query = query.filter(ServiceProfile.location.ilike(f"%{location}%"))
        
    return query.order_by(desc(ServiceProfile.rating)).offset(skip).limit(limit).all()


@router.get("/home/trending", response_model=List[ServiceProfileRead])
def get_trending_services(db: Session = Depends(get_db)):
    """Get service profiles with most bookings in last 30 days."""
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    trending_ids = db.query(
        ServiceBooking.service_profile_id,
        func.count(ServiceBooking.id).label('booking_count')
    ).filter(
        ServiceBooking.created_at >= thirty_days_ago
    ).group_by(
        ServiceBooking.service_profile_id
    ).order_by(
        desc('booking_count')
    ).limit(10).all()
    
    if not trending_ids:
        # Fallback to highest rated services
        return db.query(ServiceProfile).filter(
            ServiceProfile.active_status == True
        ).order_by(desc(ServiceProfile.rating), desc(ServiceProfile.total_reviews)).limit(10).all()
        
    ids = [t[0] for t in trending_ids]
    profiles = db.query(ServiceProfile).filter(ServiceProfile.id.in_(ids)).all()
    profiles.sort(key=lambda x: ids.index(x.id))
    
    return profiles


@router.get("/home/recommended", response_model=List[ServiceProfileRead])
def get_recommended_services(db: Session = Depends(get_db)):
    """Get recommended services (Verified + High Rating)."""
    return db.query(ServiceProfile).filter(
        ServiceProfile.active_status == True,
        ServiceProfile.is_verified == True
    ).order_by(
        desc(ServiceProfile.rating), 
        desc(ServiceProfile.created_at)
    ).limit(10).all()


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

@router.post("/leads", response_model=ServiceLeadRead)
def create_service_lead(
    lead_in: ServiceLeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Post a new service lead and auto-distribute to top providers."""
    # Note: importing the models here to avoid circular dependencies if they exist, but they are already imported at the top.
    from ...models.services import ServiceLead, LeadAssignment
    
    new_lead = ServiceLead(
        user_id=current_user.id,
        category_id=lead_in.category_id,
        location=lead_in.location,
        description=lead_in.description
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    
    # Auto Lead Distribution Logic
    # Find active providers in this category, sort by rating, limit to 5
    top_profiles = db.query(ServiceProfile).filter(
        ServiceProfile.category_id == lead_in.category_id,
        ServiceProfile.active_status == True
    ).order_by(desc(ServiceProfile.rating)).limit(5).all()
    
    for profile in top_profiles:
        # Don't assign to self
        if profile.provider_id == current_user.id:
            continue
            
        assignment = LeadAssignment(
            lead_id=new_lead.id,
            provider_id=profile.provider_id,
            status="pending"
        )
        db.add(assignment)
        
    db.commit()
    return new_lead

@router.get("/leads", response_model=List[LeadAssignmentRead])
def get_provider_leads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all leads assigned to the current provider."""
    from ...models.services import LeadAssignment
    return db.query(LeadAssignment).filter(
        LeadAssignment.provider_id == current_user.id
    ).order_by(desc(LeadAssignment.created_at)).all()

@router.put("/leads/{assignment_id}/{status}")
def update_lead_status(
    assignment_id: str,
    status: str, # 'accepted', 'rejected'
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Provider accepts or rejects a lead."""
    if status not in ['accepted', 'rejected']:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    from ...models.services import LeadAssignment
    assignment = db.query(LeadAssignment).filter(
        LeadAssignment.id == assignment_id,
        LeadAssignment.provider_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Lead assignment not found")
        
    assignment.status = status
    db.commit()
    return {"status": "success", "assignment_status": status}
