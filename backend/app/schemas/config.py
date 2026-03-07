from pydantic import BaseModel
from typing import Optional

class SystemConfigBase(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(BaseModel):
    value: str
    description: Optional[str] = None

class SystemConfigRead(SystemConfigBase):
    class Config:
        from_attributes = True
