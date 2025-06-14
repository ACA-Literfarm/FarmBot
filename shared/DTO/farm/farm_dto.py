from pydantic import BaseModel
from datetime import datetime

class FarmDTO(BaseModel):
    litefarm_farm_id: str
    name: str