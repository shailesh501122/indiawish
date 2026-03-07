from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EscrowBase(BaseModel):
    listing_id: str
    amount: float

class EscrowCreate(EscrowBase):
    buyer_id: str
    seller_id: str
    upi_ref: Optional[str] = None

class EscrowUpdate(BaseModel):
    status: str # held, released, disputed, refunded
    upi_ref: Optional[str] = None

class EscrowRead(EscrowCreate):
    id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
