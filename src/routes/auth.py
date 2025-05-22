from fastapi import APIRouter, HTTPException
from models.auth import LoginRequest  # Import the model from the models folder
from services.login import login_user

# Create a FastAPI router for authentication routes
router = APIRouter()

@router.post("/login")
async def login(request: LoginRequest):
    """
    Login route to authenticate the user and retrieve token, user ID, and farm ID.
    """
    result = await login_user(request.email, request.password)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result