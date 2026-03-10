from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, func, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from ..db.session import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(String)
    icon = Column(String)
    subcategories = Column(JSON, default=list) # Deprecated, use subcategory_list
    active_status = Column(Boolean, default=True)
    filter_config = Column(JSON, default=list) # List of filter definitions
    whatsapp_contact_enabled = Column(Boolean, default=True) # WhatsApp lead sharing
    
    listings = relationship("Listing", back_populates="category")
    subcategory_list = relationship("SubCategory", back_populates="category")

class SubCategory(Base):
    __tablename__ = "subcategories"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    icon = Column(String)
    category_id = Column(String, ForeignKey("categories.id"))
    active_status = Column(Boolean, default=True)

    category = relationship("Category", back_populates="subcategory_list")
    listings = relationship("Listing", back_populates="subcategory_rel")

class Listing(Base):
    __tablename__ = "listings"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String, default="Active") # Active, Sold, Suspended
    images = Column(JSON, default=list)
    active_status = Column(Boolean, default=True)
    
    category_id = Column(String, ForeignKey("categories.id"))
    subcategory = Column(String, nullable=True) # Deprecated, use subcategory_id
    subcategory_id = Column(String, ForeignKey("subcategories.id"), nullable=True)
    location = Column(String, nullable=True)
    properties = Column(JSON, default=dict) # Key-value pairs like {"brand": "Tesla"}
    listing_type = Column(String, default="sell") # 'sell' or 'rent'
    rent_price = Column(Float, nullable=True)      # Price per rent_period
    rent_period = Column(String, nullable=True)    # 'daily', 'weekly', 'monthly'
    video_url = Column(String, nullable=True)      # URL to short video reel
    user_id = Column(String, ForeignKey("users.id"))
    
    category = relationship("Category", back_populates="listings")
    subcategory_rel = relationship("SubCategory", back_populates="listings")
    owner = relationship("User")

    @property
    def category_name(self):
        return self.category.name if self.category else None

    @property
    def subcategory_name(self):
        return self.subcategory_rel.name if self.subcategory_rel else self.subcategory

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Property(Base):
    __tablename__ = "properties"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    type = Column(String, nullable=False) # Apartment, Villa, etc.
    status = Column(String, default="Active")
    images = Column(JSON, default=list)
    active_status = Column(Boolean, default=True)
    
    address = Column(String)
    city = Column(String)
    area = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    
    user_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ListingInteraction(Base):
    __tablename__ = "listing_interactions"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    listing_id = Column(String, ForeignKey("listings.id"), nullable=False)
    interaction_type = Column(String) # 'view', 'like'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Escrow(Base):
    __tablename__ = "escrows"
    id = Column(String, primary_key=True, default=generate_uuid)
    listing_id = Column(String, ForeignKey("listings.id"), nullable=False)
    buyer_id = Column(String, ForeignKey("users.id"), nullable=False)
    seller_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="held") # held, released, disputed, refunded
    upi_ref = Column(String, nullable=True) # Transaction reference from UPI
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class LocalDeal(Base):
    __tablename__ = "local_deals"
    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    discount_price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=False)
    location = Column(String, nullable=True)
    active_status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ListingView(Base):
    __tablename__ = "listing_views"
    id = Column(String, primary_key=True, default=generate_uuid)
    listing_id = Column(String, ForeignKey("listings.id"), nullable=False)
    viewer_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ListingLead(Base):
    __tablename__ = "listing_leads"
    id = Column(String, primary_key=True, default=generate_uuid)
    listing_id = Column(String, ForeignKey("listings.id"), nullable=False)
    buyer_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
