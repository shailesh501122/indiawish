from sqlalchemy import Column, String, Float, ForeignKey, DateTime, func, Text, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from ..db.session import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class ServiceCategory(Base):
    """
    Examples: Housemaid, Cook/Chef, Plumber, Electrician.
    """
    __tablename__ = "service_categories"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    icon = Column(String) # Icon URL or Material icon name
    active_status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    profiles = relationship("ServiceProfile", back_populates="category")


class ServiceProfile(Base):
    """
    A professional's offering for a specific service category.
    """
    __tablename__ = "service_profiles"

    id = Column(String, primary_key=True, default=generate_uuid)
    provider_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("service_categories.id"), nullable=False)
    
    title = Column(String, nullable=False) # e.g., "Professional Chef with 5 Years Exp."
    description = Column(Text, nullable=False)
    base_price = Column(Float, nullable=False)
    price_type = Column(String, default="hourly") # 'hourly', 'fixed_job', 'daily', 'monthly'
    
    # Provider Location/Service Area
    location = Column(String) # Center of operation (city/area name)
    service_radius_km = Column(Float, default=10.0) # How far they travel
    
    # Portfolio/Verification
    images = Column(JSON, default=list) # Portfolio images
    is_verified = Column(Boolean, default=False)
    active_status = Column(Boolean, default=True) # Provider is currently taking jobs
    
    # Metrics
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    provider = relationship("User")
    category = relationship("ServiceCategory", back_populates="profiles")
    bookings = relationship("ServiceBooking", back_populates="service_profile")


class ServiceBooking(Base):
    """
    A user's booking for a specific service profile.
    """
    __tablename__ = "service_bookings"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("users.id"), nullable=False)
    service_profile_id = Column(String, ForeignKey("service_profiles.id"), nullable=False)
    provider_id = Column(String, ForeignKey("users.id"), nullable=False) # Denormalized for easy querying
    
    # Scheduling & Location
    scheduled_date = Column(DateTime(timezone=True), nullable=False) # When the provider should arrive
    service_address = Column(Text, nullable=False) # Where to perform the service
    instructions = Column(Text, nullable=True) # Special instructions from customer
    
    # Accounting
    quoted_price = Column(Float, nullable=False) # Price locked in at time of booking
    price_type = Column(String, nullable=False)  # Copied from profile
    
    # Flow: pending -> accepted -> in_progress -> completed -> [paid] || cancelled
    status = Column(String, default="pending") 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("User", foreign_keys=[customer_id])
    provider = relationship("User", foreign_keys=[provider_id])
    service_profile = relationship("ServiceProfile", back_populates="bookings")

class ServiceLead(Base):
    __tablename__ = "service_leads"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("service_categories.id"), nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    assignments = relationship("LeadAssignment", back_populates="lead")

class LeadAssignment(Base):
    __tablename__ = "lead_assignments"
    id = Column(String, primary_key=True, default=generate_uuid)
    lead_id = Column(String, ForeignKey("service_leads.id"), nullable=False)
    provider_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending") # pending, accepted, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    lead = relationship("ServiceLead", back_populates="assignments")

