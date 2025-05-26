import logging
import json
import requests
from typing import Dict, Any, Optional, List
from config import config

async def handle_api_transaction(api_response: dict):
    """
    Handle API transaction with customer support.
    """
    note = api_response.get("note", "")
    value = api_response.get("value", "")
    transaction_type = api_response.get("type", "")
    date = api_response.get("date", "")
    crop_variety = api_response.get("crop_variety", "")
    customer = api_response.get("customer", "Cliente General")  # Default value
    
    # Log the transaction details including customer
    logging.info(f"API Transaction: Note: {note}, Value: {value}, Type: {transaction_type}, Date: {date}, Customer: {customer}")
    
    # Your existing API call logic here...
    # Make sure to include customer in the API payload if supported

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
        # TODO: Implement farm_id retrieval logic
        farm_id = "5aa78ca8-3236-11f0-a33e-66ab45519382"  # Replace with actual farm ID retrieval logic

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
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzcxMDE1YWMtMzIyZS0xMWYwLTk0YjQtNjZhYjQ1NTE5MzgyIiwiaWF0IjoxNzQ4MjUxMzMzLCJleHAiOjE3NDg4NTYxMzN9.-75_9cXDDuyIsimehvhPoo_xc5yU1mI3RQ5fkXct15U"
        
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
            logging.error(f"Error fetching revenue types: {response.status_code}")
            return None
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
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
        farm_id = "5aa78ca8-3236-11f0-a33e-66ab45519382"  # Replace with actual farm ID retrieval logic

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
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzcxMDE1YWMtMzIyZS0xMWYwLTk0YjQtNjZhYjQ1NTE5MzgyIiwiaWF0IjoxNzQ4MjUxMzMzLCJleHAiOjE3NDg4NTYxMzN9.-75_9cXDDuyIsimehvhPoo_xc5yU1mI3RQ5fkXct15U"
        
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
        logging.error(f"Request error: {e}")
        return None