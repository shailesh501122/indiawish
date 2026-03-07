from sqlalchemy import Column, String, Text
from ..db.session import Base

class SystemConfig(Base):
    __tablename__ = "system_config"

    key = Column(String, primary_key=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(String, nullable=True)
