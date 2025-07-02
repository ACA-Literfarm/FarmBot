from sqlalchemy import Column, Integer, BigInteger, Boolean, TIMESTAMP, ForeignKey, func, Index, String
from sqlalchemy.orm import relationship
from ..base import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    telegram_chat_id = Column(BigInteger, unique=False, nullable=False)
    litefarm_user_id = Column(String, ForeignKey("users.litefarm_user_id", ondelete="CASCADE"))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    selected_farm_id = Column(String(255), ForeignKey("farms.litefarm_farm_id", ondelete="SET NULL"), nullable=True)

    # Relationships
    tokens = relationship("Token", back_populates="chat_session", cascade="all, delete-orphan")

    selected_farm = relationship("Farm", backref="chat_sessions")

    __table_args__ = (
        Index("idx_chat_sessions_telegram_chat_id", "telegram_chat_id"),
        Index("idx_chat_sessions_litefarm_user_id", "litefarm_user_id"),
    )