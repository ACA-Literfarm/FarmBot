import os
import logging
import json
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
URL_LITEFARM = os.getenv("URL_LITEFARM")

async def handle_api_transaction(api_response: Dict[str, Any]) -> None:
    """
    Handle API transaction by logging the transaction details.
    
    Args:
        api_response: Dictionary containing transaction details (note, value, type)
    """
    note = api_response.get("note")
    value = api_response.get("value")
    type_ = api_response.get("type")

    logging.info(f"API Transaction: Note: {note}, Value: {value}, Type: {type_}")

async def request_expense_types() -> Optional[List[Dict[str, Any]]]:
    """
    Request expense types from the LiteFarm API.
    
    Returns:
        List of expense types if successful, None if there was an error
    """
    if not URL_LITEFARM:
        logging.error("URL_LITEFARM environment variable not set")
        return None
        
    try:
        response = requests.get(f"{URL_LITEFARM}/expense_type/all")
        if response.status_code == 200:
            data = response.json()
            if not data:  # Check if response is empty
                logging.error("Expense types response is empty")
                return None
            return data
        else:
            logging.error(f"Error fetching expense types: {response.status_code}")
            return None
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return None