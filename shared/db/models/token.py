from sqlalchemy import Column, Integer, Text, TIMESTAMP, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship
from ..base import Base

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    token = Column(Text, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    chat_session = relationship("ChatSession", back_populates="tokens")