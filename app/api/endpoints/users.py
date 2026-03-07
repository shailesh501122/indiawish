from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from ...db.session import get_db
from ...models.user import User
from ...api.deps import get_current_user
from ...schemas.auth import UserResponse
from ...schemas.marketplace import SellerProfile, ListingRead, CategoryRead, UserBasic
from ...models.user import Follower
from ...models.marketplace import Listing, Category

router = APIRouter()

class ProfileUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phoneNumber: Optional[str] = None
    profilePicUrl: Optional[str] = None

@router.patch("/profile", response_model=UserResponse)
def update_profile(
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        if profile_data.firstName is not None:
            current_user.first_name = profile_data.firstName
        if profile_data.lastName is not None:
            current_user.last_name = profile_data.lastName
        if profile_data.phoneNumber is not None:
            current_user.phone_number = profile_data.phoneNumber
        if profile_data.profilePicUrl is not None:
            current_user.profile_pic_url = profile_data.profilePicUrl
            
        db.commit()
        db.refresh(current_user)
        
        follower_count = db.query(Follower).filter(Follower.followed_id == current_user.id).count()
        following_count = db.query(Follower).filter(Follower.follower_id == current_user.id).count()
        
        return {
            "id": current_user.id,
            "email": current_user.email,
            "firstName": current_user.first_name,
            "lastName": current_user.last_name,
            "phoneNumber": current_user.phone_number,
            "profilePicUrl": current_user.profile_pic_url,
            "roles": current_user.roles.split(","),
            "created_at": current_user.created_at,
            "last_seen": current_user.last_seen,
            "follower_count": follower_count,
            "following_count": following_count,
            "is_elite": getattr(current_user, 'is_elite', False) or False
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.post("/toggle-elite", response_model=UserResponse)
def toggle_elite(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.is_elite = not getattr(current_user, 'is_elite', False)
    db.commit()
    db.refresh(current_user)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "firstName": current_user.first_name,
        "lastName": current_user.last_name,
        "phoneNumber": current_user.phone_number,
        "profilePicUrl": current_user.profile_pic_url,
        "roles": current_user.roles.split(","),
        "created_at": current_user.created_at,
        "is_elite": current_user.is_elite
    }

@router.get("/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    follower_count = db.query(Follower).filter(Follower.followed_id == current_user.id).count()
    following_count = db.query(Follower).filter(Follower.follower_id == current_user.id).count()
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "firstName": current_user.first_name,
        "lastName": current_user.last_name,
        "phoneNumber": current_user.phone_number,
        "profilePicUrl": current_user.profile_pic_url,
        "roles": current_user.roles.split(","),
        "created_at": current_user.created_at,
        "last_seen": current_user.last_seen,
        "follower_count": follower_count,
        "following_count": following_count,
        "is_elite": getattr(current_user, 'is_elite', False) or False
    }

@router.get("/{user_id}/profile", response_model=SellerProfile)
def get_seller_profile(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    listings = db.query(Listing).filter(Listing.user_id == user_id, Listing.status == "Active", Listing.active_status == True).all()
    
    follower_count = db.query(Follower).filter(Follower.followed_id == user_id).count()
    following_count = db.query(Follower).filter(Follower.follower_id == user_id).count()
    
    is_following = False
    is_followed_by = False
    if current_user:
        is_following = db.query(Follower).filter(Follower.follower_id == current_user.id, Follower.followed_id == user_id).first() is not None
        is_followed_by = db.query(Follower).filter(Follower.follower_id == user_id, Follower.followed_id == current_user.id).first() is not None
        
    user_basic = UserBasic(
        id=target_user.id,
        first_name=target_user.first_name,
        last_name=target_user.last_name,
        email=target_user.email,
        phone_number=target_user.phone_number,
        profile_pic_url=target_user.profile_pic_url,
        created_at=target_user.created_at,
        last_seen=target_user.last_seen,
        follower_count=follower_count,
        following_count=following_count,
        is_elite=getattr(target_user, 'is_elite', False) or False
    )
    
    return {
        "user": user_basic,
        "listings": listings,
        "follower_count": follower_count,
        "following_count": following_count,
        "is_following": is_following,
        "is_followed_by": is_followed_by
    }

@router.post("/{user_id}/follow")
def follow_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cant follow yourself")
        
    existing_follow = db.query(Follower).filter(Follower.follower_id == current_user.id, Follower.followed_id == user_id).first()
    
    if existing_follow:
        db.delete(existing_follow)
        db.commit()
        return {"message": "Unfollowed successfully", "is_following": False}
    else:
        new_follow = Follower(follower_id=current_user.id, followed_id=user_id)
        db.add(new_follow)
        db.commit()
        return {"message": "Followed successfully", "is_following": True}
