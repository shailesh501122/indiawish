from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON, func
import uuid
from ..db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'chat', 'listing', 'system', 'booking'
    data = Column(JSON, nullable=True)     # Extra data like listing_id, conversation_id
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
