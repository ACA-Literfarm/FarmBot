from sqlalchemy import Column, TIMESTAMP, String
from ..base import Base


class User(Base):
    __tablename__ = "users"

    litefarm_user_id = Column(String, nullable=False, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()")