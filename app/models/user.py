from sqlalchemy import Column, String, Boolean, DateTime, Float, func, ForeignKey, Enum
from sqlalchemy.orm import relationship
from ..db.session import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String)
    profile_pic_url = Column(String)
    is_active = Column(Boolean, default=True)
    active_status = Column(Boolean, default=True)
    roles = Column(String, default="User") # Storing as comma-separated string for simplicity in porting
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=True)
    is_elite = Column(Boolean, default=False)
    verification_level = Column(String, default="unverified") # Badge level: unverified -> phone -> id -> top_seller

    # Referrals
    referral_code = Column(String, unique=True, index=True, nullable=True)
    referred_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    referral_reward_balance = Column(Float, default=0.0)

    # Followers / Following
    followers_rel = relationship(
        "Follower",
        foreign_keys="[Follower.followed_id]",
        back_populates="followed"
    )
    following_rel = relationship(
        "Follower",
        foreign_keys="[Follower.follower_id]",
        back_populates="follower"
    )

class Follower(Base):
    __tablename__ = "followers"
    id = Column(String, primary_key=True, default=generate_uuid)
    follower_id = Column(String, ForeignKey("users.id"), nullable=False)
    followed_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following_rel")
    followed = relationship("User", foreign_keys=[followed_id], back_populates="followers_rel")

class ReferralTransaction(Base):
    __tablename__ = "referral_transactions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    referrer_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    referred_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    reward_amount = Column(Float, nullable=False)
    status = Column(String, default="pending") # pending, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    referrer = relationship("User", foreign_keys=[referrer_user_id])
    referred = relationship("User", foreign_keys=[referred_user_id])
