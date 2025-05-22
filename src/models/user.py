from pydantic import BaseModel

class UserSession(BaseModel):
    token: str
    farm_id: str  # Change from int to str