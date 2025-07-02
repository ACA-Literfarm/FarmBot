# shared/DTO/token/token_dto.py
from pydantic import BaseModel
from datetime import datetime

class TokenCreateDTO(BaseModel):
    chat_session_id: int
    token: str
    expires_at: datetime
