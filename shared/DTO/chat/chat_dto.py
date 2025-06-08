# shared/DTO/chat/chat_dto.py
from pydantic import BaseModel
from uuid import UUID

class ChatSessionCreateDTO(BaseModel):
    litefarm_user_id: UUID
    telegram_chat_id: int