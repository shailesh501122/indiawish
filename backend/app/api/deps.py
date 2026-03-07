from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from ..db.session import SessionLocal
from ..core.security import SECRET_KEY, ALGORITHM
from ..models.user import User

security = HTTPBearer()

from ..db.session import get_db
        
def get_current_user(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub") or payload.get("nameid")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # Update last seen
    try:
        from datetime import datetime
        user.last_seen = datetime.utcnow()
        db.commit() # Commit last_seen update within the same session
        db.refresh(user)
    except Exception as e:
        print(f"Error updating last_seen: {e}")
    
    return user

def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if "Admin" not in current_user.roles.split(","):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    return current_user

