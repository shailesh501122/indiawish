from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db
from ...models.marketplace import Property
from ...schemas.marketplace import PropertyRead, PropertyCreate
from ...api.deps import get_current_user
from ...models.user import User

router = APIRouter()

@router.get("", response_model=List[PropertyRead])
def get_properties(db: Session = Depends(get_db)):
    return db.query(Property).filter(Property.status == "Active").all()

@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: str, db: Session = Depends(get_db)):
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    return property_obj

@router.post("", response_model=PropertyRead)
def create_property(
    property_in: PropertyCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_property = Property(
        **property_in.dict(),
        user_id=current_user.id
    )
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
    return new_property
