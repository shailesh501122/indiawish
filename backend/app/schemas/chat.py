from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserBasic(BaseModel):
    id: str
    first_name: str
    last_name: str
    profile_pic_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    conversation_id: str

class MessageRead(MessageBase):
    id: str
    sender_id: str
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True

class ConversationRead(BaseModel):
    id: str
    participant_one_id: str
    participant_two_id: str
    listing_id: Optional[str] = None
    property_id: Optional[str] = None
    last_message: Optional[str] = None
    updated_at: Optional[datetime] = None
    other_user: UserBasic

    class Config:
        from_attributes = True
