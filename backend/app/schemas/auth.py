from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# DTO for logging in
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    idToken: str

# DTO for registering
class RegisterRequest(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    phoneNumber: Optional[str] = None
    profilePicUrl: Optional[str] = None

    class Config:
        populate_by_name = True

# Response DTO matching the User object sent back by the .NET API
class UserResponse(BaseModel):
    id: str
    email: str
    firstName: str
    lastName: str
    phoneNumber: Optional[str] = None
    profilePicUrl: Optional[str] = None
    roles: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    follower_count: int = 0
    following_count: int = 0
    is_elite: bool = False

    class Config:
        from_attributes = True

# Main Auth Response wrapper
class AuthResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserResponse
