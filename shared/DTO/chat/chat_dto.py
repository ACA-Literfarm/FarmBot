# shared/DTO/chat/chat_dto.py
from pydantic import BaseModel

class ChatSessionCreateDTO(BaseModel):
    litefarm_user_id: str
    telegram_chat_id: int