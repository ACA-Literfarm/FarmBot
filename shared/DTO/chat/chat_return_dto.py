# shared/DTO/chat/chat_return_dto.py
from pydantic import BaseModel
from datetime import datetime

class ChatSessionOutDTO(BaseModel):
    id: int
    litefarm_user_id: str
    telegram_chat_id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}