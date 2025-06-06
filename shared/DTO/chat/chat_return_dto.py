# shared/DTO/chat/chat_return_dto.py
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class ChatSessionOutDTO(BaseModel):
    id: int
    litefarm_user_id: UUID
    telegram_chat_id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}