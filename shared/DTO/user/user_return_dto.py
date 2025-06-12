from datetime import datetime
from pydantic import BaseModel

class UserOutDTO(BaseModel):
    litefarm_user_id: str
    created_at: datetime

    model_config = {
        "from_attributes": True  # Pydantic v2 replacement for orm_mode=True
    }
