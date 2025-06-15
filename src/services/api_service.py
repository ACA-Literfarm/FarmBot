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

async def handle_api_transaction(api_response: dict, clasificacion: str, message: Message) -> None:
    """
    Handle API transaction with customer support.
    """
    note = api_response.get("note", "")
    value = api_response.get("value", "")
    transaction_type = api_response.get("type", "")
    date = api_response.get("date", "")
    crop_variety = api_response.get("crop_variety", "")
    customer = api_response.get("customer", "Cliente General")  
    chat_session_id = message.chat.id  # Use chat.id instead of from_user.id for telegram_chat_id
    
    if clasificacion == "gasto":
        await register_expense(
            expense_date=date,
            expense_type_id=transaction_type,
            farm_id=config.FARM_ID,  # Assuming FARM_ID is set in config
            note=note,
            value=float(value),
            chat_session_id=chat_session_id 
        )
    elif clasificacion == "ingreso":
        await register_sale(
            farm_id=config.FARM_ID,  # Assuming FARM_ID is set in config
            customer_name=customer,
            sale_date=date,
            revenue_type_id=int(transaction_type),
            note=note,
            crop_variety_sale=[{
                "crop_variety_id": crop_variety,
                "quantity": 1,  # Assuming quantity is 1 for simplicity
                "quantity_unit": "kg",  # Assuming unit is kg for simplicity
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
        "expense_date": datetime.strptime(expense_date, "%Y-%m-%d").isoformat() + "Z",
        "expense_type_id": expense_type_id,
        "farm_id": farm_id,
        "note": note,
        "value": float(value)
    }]

    try:
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
        "sale_date": datetime.strptime(sale_date, "%Y-%m-%d").isoformat() + "Z",
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
async def request_expense_types() -> Optional[List[Dict[str, Any]]]:
    """
    Request expense types from the LiteFarm API.
    
    Returns:
        List of expense types if successful, None if there was an error
    """
    if not config.URL_LITEFARM:
        logging.error("URL_LITEFARM environment variable not set")
        return None
        
    try:
        response = requests.get(f"{config.URL_LITEFARM}/expense_type/all")
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
async def request_revenue_types() -> Optional[List[Dict[str, Any]]]:
    """
    Request revenue types from the LiteFarm API.
    
    Returns:
        List of revenue types if successful, None if there was an error
    """

    if not config.URL_LITEFARM:
        logging.error("URL_LITEFARM environment variable not set")
        return None
        
    try:
        farm_id = config.FARM_ID

        """ 
        Header format must look like this:
            Content-Type:application/json
            User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
            Accept-Language:en
            farm_id:{farm_id}
        And an authorization Bearer header with a valid token.
        The farm_id is used to fetch revenue types specific to a farm.
        """

        token=config.LOGIN_TOKEN
        
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
async def request_crop_varieties() -> Optional[List[Dict[str, Any]]]:
    """
    Request crop varieties from the LiteFarm API.
    
    Returns:
        List of crop varieties if successful, None if there was an error
    """

    if not config.URL_LITEFARM:
        logging.error("URL_LITEFARM environment variable not set")
        return None
        
    try:
        # TODO: Implement farm_id retrieval logic
        farm_id = config.FARM_ID  # Replace with actual farm ID retrieval logic

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
        token=config.LOGIN_TOKEN
        
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
            data = response.json()
            ## Validate if the response contains expected data (list of crop varieties)
            if not data:  # Check if response is empty
                logging.error("Crop varieties response is empty")
                return None
            
            return data
        else:
            logging.error(f"Error fetching crop varieties: {response.status_code}")
            return None
    except requests.RequestException as e:
        logging.error(f"Crop varieties request error: {e}")
        return None