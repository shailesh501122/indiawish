from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ServiceCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    active_status: bool = True

class ServiceCategoryRead(ServiceCategoryBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class ServiceCategoryCreate(ServiceCategoryBase):
    pass

class ServiceCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    active_status: Optional[bool] = None

class ServiceProfileRead(BaseModel):
    id: str
    provider_id: str
    category_id: str
    title: str
    description: str
    base_price: float
    price_type: str
    location: Optional[str]
    service_radius_km: float
    images: List[str]
    is_verified: bool
    rating: float
    total_reviews: int

    class Config:
        from_attributes = True

class ServiceBookingCreate(BaseModel):
    service_profile_id: str
    scheduled_date: datetime
    service_address: str
    instructions: Optional[str]

class ServiceBookingRead(BaseModel):
    id: str
    customer_id: str
    service_profile_id: str
    provider_id: str
    scheduled_date: datetime
    service_address: str
    instructions: Optional[str]
    quoted_price: float
    price_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
