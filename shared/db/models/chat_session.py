from sqlalchemy import Column, Integer, BigInteger, Boolean, TIMESTAMP, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..base import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    telegram_chat_id = Column(BigInteger, unique=True, nullable=False)
    litefarm_user_id = Column(UUID(as_uuid=True), ForeignKey("users.litefarm_user_id", ondelete="CASCADE"))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    tokens = relationship("Token", back_populates="chat_session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_chat_sessions_telegram_chat_id", "telegram_chat_id"),
        Index("idx_chat_sessions_litefarm_user_id", "litefarm_user_id"),
    )