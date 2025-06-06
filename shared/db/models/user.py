from sqlalchemy import Column, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from ..base import Base


class User(Base):
    __tablename__ = "users"

    litefarm_user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()")