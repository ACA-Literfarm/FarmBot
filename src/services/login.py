import logging
import httpx
from config import API_REQUEST_ROUTE
from models.user import UserSession

# Dictionary to store user session data
user_sessions: dict[str, UserSession] = {}

async def login_user(email: str, password: str) -> dict:
    """
    Logs in the user and retrieves the token, user ID, and farm ID.
    """
    try:
        login_url = str(API_REQUEST_ROUTE) + "login/"

        # Prepare the JSON payload
        payload = {
            "user": {
                "email": email,
                "password": password
            },
            "screenSize": {
                "screen_width": 1920,
                "screen_height": 1080
            }
        }

        # Prepare the headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }

        # Send the login request
        async with httpx.AsyncClient() as client:
            response = await client.post(login_url, json=payload, headers=headers)

        # Check if the login was successful
        if response.status_code == 200:
            data = response.json()

            # Extract the token, user ID, and farm ID
            token = data.get("id_token")
            user = data.get("user", {})
            farms = data.get("farms", [])

            user_id = user.get("user_id")
            farm_id = str(farms[0].get("farm_id")) if farms and farms[0].get("farm_id") else "0"  # Default to "0" if no farm_id is found

            if not all([token, user_id, farm_id]):
                raise ValueError("Missing required fields in the login response.")

            # Store the session data
            if farm_id is None:
                raise ValueError("Farm ID is missing in the login response.")
            user_sessions[user_id] = UserSession(token=token, farm_id=farm_id)

            logging.info(f"User {user_id} logged in successfully.")
            return {"token": token, "user_id": user_id, "farm_id": farm_id}
        else:
            logging.error(f"Login failed: {response.text}")
            return {"error": "Invalid credentials or server error."}

    except Exception as e:
        logging.error(f"Error during login: {e}")
        return {"error": "An error occurred during login."}