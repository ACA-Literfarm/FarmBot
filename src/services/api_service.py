import logging
import json
import requests
from typing import Dict, Any, Optional, List
from config import config

async def handle_api_transaction(api_response: Dict[str, Any]) -> None:
    """
    Handle API transaction by logging the transaction details.
    
    Args:
        api_response: Dictionary containing transaction details (note, value, type, date)
    """
    note = api_response.get("note")
    value = api_response.get("value")
    type_ = api_response.get("type")
    date_ = api_response.get("date")

    logging.info(f"API Transaction: Note: {note}, Value: {value}, Type: {type_}, Date: {date_}")

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
        logging.error(f"Request error: {e}")
        return None