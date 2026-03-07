from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from ...db.session import get_db
from ...models.user import User
from ...schemas.auth import LoginRequest, RegisterRequest, AuthResponse, UserResponse, GoogleAuthRequest
from ...core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)
from jose import jwt, JWTError

router = APIRouter()

@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "accessToken": access_token,
        "refreshToken": create_refresh_token(user.id),
        "user": {
            "id": user.id,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "phoneNumber": user.phone_number,
            "profilePicUrl": user.profile_pic_url,
            "roles": user.roles.split(","),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_elite": getattr(user, 'is_elite', False) or False
        }
    }

@router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == request.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    new_user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        first_name=request.firstName,
        last_name=request.lastName,
        phone_number=request.phoneNumber,
        profile_pic_url=request.profilePicUrl,
        roles="User"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=new_user.id, expires_delta=access_token_expires
    )
    
    return {
        "accessToken": access_token,
        "refreshToken": create_refresh_token(new_user.id),
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "firstName": new_user.first_name,
            "lastName": new_user.last_name,
            "phoneNumber": new_user.phone_number,
            "profilePicUrl": new_user.profile_pic_url,
            "roles": ["User"],
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
            "is_elite": False
        }
    }
@router.post("/refresh", response_model=AuthResponse)
def refresh_token(refreshToken: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refreshToken, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return {
            "accessToken": create_access_token(user.id),
            "refreshToken": create_refresh_token(user.id),
            "user": {
                "id": user.id,
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "phoneNumber": user.phone_number,
                "profilePicUrl": user.profile_pic_url,
                "roles": user.roles.split(","),
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "is_elite": getattr(user, 'is_elite', False) or False
            }
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/google-login", response_model=AuthResponse)
def google_login(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    import uuid
    
    GOOGLE_CLIENT_ID = "768464272204-i10dbub1od9nupedmtdku13gsl3qheb1.apps.googleusercontent.com"
    
    try:
        # Real verification with the provided Client ID
        idinfo = id_token.verify_oauth2_token(request.idToken, google_requests.Request(), GOOGLE_CLIENT_ID)
        
        email = idinfo['email']
        first_name = idinfo.get('given_name', 'Google')
        last_name = idinfo.get('family_name', 'User')
        profile_pic = idinfo.get('picture')
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash(uuid.uuid4().hex), # Random password
                first_name=first_name,
                last_name=last_name,
                profile_pic_url=profile_pic,
                roles="User"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        access_token = create_access_token(subject=user.id)
        
        return {
            "accessToken": access_token,
            "refreshToken": create_refresh_token(user.id),
            "user": {
                "id": user.id,
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "phoneNumber": user.phone_number,
                "profilePicUrl": user.profile_pic_url,
                "roles": user.roles.split(","),
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "is_elite": getattr(user, 'is_elite', False) or False
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google login failed: {str(e)}")
