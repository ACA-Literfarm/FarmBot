from uuid import UUID
from pydantic import BaseModel

class CreateUserDTO(BaseModel):
    litefarm_user_id: UUID
