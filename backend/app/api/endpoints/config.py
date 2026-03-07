from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db
from ...models.config import SystemConfig
from ...schemas.config import SystemConfigRead, SystemConfigCreate, SystemConfigUpdate
from ..deps import get_current_admin

router = APIRouter()

@router.get("", response_model=List[SystemConfigRead])
def get_all_configs(db: Session = Depends(get_db)):
    """Publicly accessible configurations (e.g. colors, but exclude sensitive keys in production)"""
    return db.query(SystemConfig).all()

@router.get("/{key}", response_model=SystemConfigRead)
def get_config(key: str, db: Session = Depends(get_db)):
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config

@router.post("", response_model=SystemConfigRead)
def create_config(
    config_in: SystemConfigCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    existing = db.query(SystemConfig).filter(SystemConfig.key == config_in.key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Configuration key already exists")
    
    config = SystemConfig(**config_in.dict())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config

@router.put("/{key}", response_model=SystemConfigRead)
def update_config(
    key: str,
    config_in: SystemConfigUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    for field, value in config_in.dict(exclude_unset=True).items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    return config

@router.delete("/{key}")
def delete_config(
    key: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    db.delete(config)
    db.commit()
    return {"message": "Configuration deleted"}
