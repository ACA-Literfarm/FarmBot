# shared/DTO/token/token_return_dto.py
from pydantic import BaseModel
from datetime import datetime

class TokenOutDTO(BaseModel):
    id: int
    chat_session_id: int
    token: str
    expires_at: datetime
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}
