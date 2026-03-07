from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .user import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    participant_one_id = Column(String, ForeignKey("users.id"))
    participant_two_id = Column(String, ForeignKey("users.id"))
    listing_id = Column(String, ForeignKey("listings.id"), nullable=True)
    property_id = Column(String, ForeignKey("properties.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active_status = Column(Boolean, default=True)

    participant_one = relationship("User", foreign_keys=[participant_one_id])
    participant_two = relationship("User", foreign_keys=[participant_two_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    listing = relationship("Listing", foreign_keys=[listing_id])
    property = relationship("Property", foreign_keys=[property_id])

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    sender_id = Column(String, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    active_status = Column(Boolean, default=True)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")
