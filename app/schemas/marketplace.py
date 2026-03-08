from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBasic(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    profile_pic_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    follower_count: int = 0
    following_count: int = 0
    is_elite: bool = False
    class Config:
        from_attributes = True

class SubCategoryBase(BaseModel):
    name: str
    icon: Optional[str] = None
    active_status: bool = True

class SubCategoryCreate(SubCategoryBase):
    category_id: str

class SubCategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    active_status: Optional[bool] = None

class SubCategoryRead(SubCategoryBase):
    id: str
    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    active_status: bool = True
    filter_config: Optional[List[dict]] = []

class CategoryRead(CategoryBase):
    id: str
    subcategory_list: List[SubCategoryRead] = []
    class Config:
        from_attributes = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    active_status: Optional[bool] = None
    filter_config: Optional[List[dict]] = None

class ListingBase(BaseModel):
    title: str
    description: str
    price: float
    category_id: Optional[str] = None
    subcategory: Optional[str] = None
    subcategory_id: Optional[str] = None
    location: Optional[str] = None
    properties: dict = {}
    listing_type: str = "sell"
    rent_price: Optional[float] = None
    rent_period: Optional[str] = None
    video_url: Optional[str] = None
    images: List[str] = []

class ListingCreate(ListingBase):
    pass

class ListingRead(ListingBase):
    id: str
    status: str
    user_id: str
    category_name: Optional[str] = None
    subcategory_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner: Optional[UserBasic] = None
    category: Optional[CategoryRead] = None
    class Config:
        from_attributes = True

class PropertyBase(BaseModel):
    title: str
    description: str
    price: float
    type: str
    address: Optional[str] = None
    city: Optional[str] = None
    area: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    images: List[str] = []

class PropertyCreate(PropertyBase):
    pass

class PropertyRead(PropertyBase):
    id: str
    status: str
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner: Optional[UserBasic] = None
    class Config:
        from_attributes = True

class SellerProfile(BaseModel):
    user: UserBasic
    listings: List[ListingRead] = []
    follower_count: int = 0
    following_count: int = 0
    is_following: bool = False
    is_followed_by: bool = False
    class Config:
        from_attributes = True
