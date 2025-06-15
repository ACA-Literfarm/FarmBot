# shared/models/farm.py

from sqlalchemy import Column, String, Text, TIMESTAMP, func
from sqlalchemy.orm import relationship
from ..base import Base 

class Farm(Base):
    __tablename__ = 'farms'

    litefarm_farm_id = Column(String(255), primary_key=True)
    name = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())