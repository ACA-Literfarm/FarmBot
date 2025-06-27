import logging
import json
import requests
from typing import Dict, Any, Optional, List
from config import config
from datetime import datetime
import sys
import os
from aiogram.types import Message

# Agrega el path al root del proyecto para que shared sea visible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.repositories.token_repository import TokenRepository
from shared.repositories.chat_repository import ChatSessionRepository
from shared.db.session import AsyncSessionLocal

async def get_selected_farm_id(chat_session_id: int) -> str:
    """Get the selected farm ID for the given chat session."""
    try:
        # Import locally to avoid circular import
        from shared.repositories.farm_repository import FarmRepository
        from shared.repositories.chat_repository import ChatSessionRepository
        from shared.services.farm_selection_service import FarmSelectionService
        
        farm_service = FarmSelectionService(
            repo_factory=FarmRepository,
            chat_session_repo_factory=ChatSessionRepository
        )
        
        async with AsyncSessionLocal() as session:
            selected_farm = await farm_service.get_selected_farm(
                chat_id=chat_session_id,
                session=session
            )
            if selected_farm:
                return str(selected_farm.litefarm_farm_id)
            return ""
    except Exception as e:
        logging.error(f"Error getting selected farm for chat {chat_session_id}: {e}")
        return ""

async def get_valid_token_for_chat(telegram_chat_id: int):
    try:
        async with AsyncSessionLocal() as session:
            chatRepo = ChatSessionRepository(session)
            tokenRepo = TokenRepository(session)
            chat_session = await chatRepo.get_chat_by_telegram_chat_id(telegram_chat_id)
            chat_session_id = chat_session.id  
            tokens = await tokenRepo.get_valid_tokens_by_chat_session(chat_session_id)
            if tokens:
                return tokens[0].token  # Devuelve el primer token válido encontrado
            return None
    except Exception as e:
        return None
    
def format_iso_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%Y-%m-%dT06:00:00.000Z")

async def handle_api_transaction(api_response: dict, clasificacion: str, message: Message) -> None:
    """
    Handle API transaction with customer support.
    """
    note = api_response.get("note", "")
    value = api_response.get("value", "")
    transaction_type = api_response.get("type", "")
    date = api_response.get("date", "")
    crop_variety = api_response.get("crop_variety", "")
    customer = api_response.get("customer", "")
    quantity = api_response.get("quantity", 1)
    quantity_unit = api_response.get("quantity_unit", "kg")

    chat_session_id = message.chat.id  # Use chat.id instead of from_user.id for telegram_chat_id
    
    # Get selected farm ID for this chat
    farm_id = await get_selected_farm_id(chat_session_id)
    if not farm_id:
        logging.error(f"No selected farm found for chat {chat_session_id}")
        return
    
    if clasificacion == "gasto":
        await register_expense(
            expense_date=date,
            expense_type_id=transaction_type,
            farm_id=farm_id,
            note=note,
            value=float(value),
            chat_session_id=chat_session_id 
        )
    elif clasificacion == "ingreso":
        await register_sale(
            farm_id=farm_id,
            customer_name=customer,
            sale_date=date,
            revenue_type_id=int(transaction_type),
            note=note,
            crop_variety_sale=[{
                "crop_variety_id": crop_variety,
                "quantity": int(quantity),
                "quantity_unit": quantity_unit,
                "sale_value": float(value)
            }],
            chat_session_id=chat_session_id
        )

async def register_expense(
        expense_date: str,
        expense_type_id: int,
        farm_id: str,
        note: str,
        value: float,
        chat_session_id: int
    ) -> Optional[Dict[str, Any]]:
    """
    Register an expense in LiteFarm via POST request.
    """
    token = await get_valid_token_for_chat(chat_session_id)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en",
        "farm_id": farm_id,
        "Authorization": f"Bearer {token}"
    }

    payload = [{
        "expense_date": format_iso_date(expense_date),
        "expense_type_id": expense_type_id,
        "farm_id": farm_id,
        "note": note,
        "value": float(value)
    }]

    try:
        print(payload)
        response = requests.post(
            f"{config.URL_LITEFARM}/expense/farm/{farm_id}",
            headers=headers,
            data=json.dumps(payload)
        )
        if response.status_code == 201:
            logging.info("Expense registered successfully")
            try: # This is because the response might be empty
                return response.json() if response.content else {"status": "success", "message": "Empty response"}
            except ValueError:
                return {"status": "success", "message": "No JSON returned"}
        else:
            logging.error(f"Error registering expense: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e: 
        logging.error(f"Expense request error: {e}") #Dont know why this exception is triggering
        return None

async def register_sale(
    farm_id: str,
    customer_name: str,
    sale_date: str,
    revenue_type_id: int,
    note: str,
    crop_variety_sale: list,
    chat_session_id: int
) -> Optional[Dict[str, Any]]:
    """
    Register a sale in LiteFarm via POST request.
    """
    token = await get_valid_token_for_chat(chat_session_id)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en",
        "farm_id": farm_id,
        "Authorization": f"Bearer {token}" 
    }

    payload = {
        "farm_id": farm_id,
        "customer_name": customer_name,
        "sale_date": sale_date,
        "revenue_type_id": revenue_type_id,
        "note": note,
        "crop_variety_sale": crop_variety_sale
    }

    try:
        response = requests.post(
            f"{config.URL_LITEFARM}/sale",
            headers=headers,
            data=json.dumps(payload)
        )
        if response.status_code == 201:
            logging.info("Sale registered successfully")
            return response.json()
        else:
            logging.error(f"Error registering sale: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        logging.error(f"Sale request error: {e}")
        return None

## Request expense types from LiteFarm API
async def request_expense_types(chat_session_id: int) -> Optional[List[Dict[str, Any]]]:
    """
    Request expense types from the LiteFarm API.
    Args:
        chat_session_id: Telegram chat ID to get the user's token
    
    Returns:
        List of expense types if successful, None if there was an error
    """
    if not config.URL_LITEFARM:
        logging.error("URL_LITEFARM environment variable not set")
        return None
        
    try:
        farm_id = await get_selected_farm_id(chat_session_id);
        token = await get_valid_token_for_chat(chat_session_id)
        if not token:
            logging.error(f"No valid token found for chat_session_id: {chat_session_id}")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en",
            "farm_id": farm_id,
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(f"{config.URL_LITEFARM}/expense_type/all/{farm_id}", headers=headers)
        print(response.json())
        if response.status_code == 200:
            data = response.json()
            ## Validate if the response contains expected data (list of expense types)
            if not data:  # Check if response is empty
                logging.error("Expense types response is empty")
                return None
            return data
        else:
            logging.error(f"Error fetching expense types: {response.status_code}")
            return None
    except requests.RequestException as e:
        logging.error(f"Expense request error: {e}")
        return None

# Request revenue types from LiteFarm API
async def request_revenue_types(chat_session_id: int) -> Optional[List[Dict[str, Any]]]:
    """
    Request revenue types from the LiteFarm API.
    
    Args:
        chat_session_id: Telegram chat ID to get the user's token
    
    Returns:
        List of revenue types if successful, None if there was an error
    """

    if not config.URL_LITEFARM:
        logging.error("URL_LITEFARM environment variable not set")
        return None
        
    try:
        # Get selected farm ID for this chat
        farm_id = await get_selected_farm_id(chat_session_id)
        if not farm_id:
            logging.error(f"No selected farm found for chat {chat_session_id}")
            return None

        """ 
        Header format must look like this:
            Content-Type:application/json
            User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
            Accept-Language:en
            farm_id:{farm_id}
        And an authorization Bearer header with a valid token.
        The farm_id is used to fetch revenue types specific to a farm.
        """

        token = await get_valid_token_for_chat(chat_session_id)
        if not token:
            logging.error(f"No valid token found for chat_session_id: {chat_session_id}")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en",
            "farm_id": farm_id,
            # Add your authorization token here if required
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(f"{config.URL_LITEFARM}/revenue_type/farm/{farm_id}", headers=headers)

        if response.status_code == 200:
            data = response.json()
            ## Validate if the response contains expected data (list of revenue types)
            if not data:  # Check if response is empty
                logging.error("Revenue types response is empty")
                return None
            
            # Add "otros" type if not present
            if not any(rt['revenue_type_id'] == 405 for rt in data):
                data.append({
                    "revenue_type_id": 405,
                    "revenue_name": "Otros",
                    "revenue_translation_key": "OTROS"
                })
            return data
        else:
            # TODO: Show error message, not just log it (Catch if the jwt token is expired)
            logging.error(f"Error fetching revenue types: {response.status_code}")
            logging.error(f"Error fetching revenue types: {response.text}")
            return None
    except requests.RequestException as e:
        logging.error(f"Revenue request error: {e}")
        return None
    
# Request crop varieties from LiteFarm API
async def request_crop_varieties(chat_session_id: int) -> Optional[List[Dict[str, Any]]]:
    """
    Request crop varieties from the LiteFarm API.
    
    Args:
        chat_session_id: Telegram chat ID to get the user's token
    
    Returns:
        List of crop varieties if successful, None if there was an error
    """

    if not config.URL_LITEFARM:
        logging.error("URL_LITEFARM environment variable not set")
        return None
        
    try:
        # Get selected farm ID for this chat
        farm_id = await get_selected_farm_id(chat_session_id)
        if not farm_id:
            logging.error(f"No selected farm found for chat {chat_session_id}")
            return None

        """ 
        Header format must look like this:
            Content-Type:application/json
            User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
            Accept-Language:en
            farm_id:{farm_id}
        And an authorization Bearer header with a valid token.
        The farm_id is used to fetch revenue types specific to a farm.
        """

        # TODO: Implement logic to retrieve the login token dynamically
        token = await get_valid_token_for_chat(chat_session_id)
        if not token:
            logging.error(f"No valid token found for chat_session_id: {chat_session_id}")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en",
            "farm_id": farm_id,
            # Add your authorization token here if required
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(f"{config.URL_LITEFARM}/crop_variety/farm/{farm_id}", headers=headers)
        if response.status_code == 200:
            data = response.json() or []  # Ensure we always return a list

            # It's valid for a farm to have 0 crop varieties configured. In that
            # scenario we simply return an empty list instead of treating it as
            # an error so that callers that only care about expense or revenue
            # types can proceed without unnecessary log noise.
            if not data:
                logging.info("Crop varieties response is empty – returning an empty list")

            return data
        else:
            logging.error(f"Error fetching crop varieties: {response.status_code}")
            return None
    except requests.RequestException as e:
        logging.error(f"Crop varieties request error: {e}")
        return None

async def request_user_farms(
        token: str,
        userId: str
        ) -> Optional[List[Dict[str, Any]]]:
    """
    Request user farms from the LiteFarm API.
    Args:
        token (str): Authorization token for the API.
        userId (str): User ID to fetch farms for.
    Returns:
        List of farms if successful, None if there was an error
    """
    if not config.URL_LITEFARM:
        logging.error("URL_LITEFARM environment variable not set")
        return None
        
    try:
        # TODO: Implement dynamic token retrieval
        # TODO: Implement dynamic user ID retrieval

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en",
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(f"{config.URL_LITEFARM}/user_farm/user/{userId}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                logging.error("User farms response is empty")
                return None
            return data
        else:
            logging.error(f"Error fetching user farms: {response.status_code}")
            return None
            
    except requests.RequestException as e:
        logging.error(f"Request error fetching farms: {e}")
        return None