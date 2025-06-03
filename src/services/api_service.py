import logging
import json
import requests
from typing import Dict, Any, Optional, List
from config import config
from datetime import datetime

async def handle_api_transaction(api_response: dict, clasificacion: str) -> None:
    """
    Handle API transaction with customer support.
    """
    note = api_response.get("note", "")
    value = api_response.get("value", "")
    transaction_type = api_response.get("type", "")
    date = api_response.get("date", "")
    crop_variety = api_response.get("crop_variety", "")
    customer = api_response.get("customer", "Cliente General")  # Default value
    
    if clasificacion == "gasto":
        await register_expense(
            expense_date=date,
            expense_type_id=transaction_type,
            farm_id=config.FARM_ID,  # Assuming FARM_ID is set in config
            note=note,
            value=float(value)
        )

async def register_expense(expense_date: str, expense_type_id: int, farm_id: str, note: str, value: float) -> Optional[Dict[str, Any]]:
    """
    Register an expense in LiteFarm via POST request.
    """

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en",
        "farm_id": farm_id,
        "Authorization": f"Bearer {config.LOGIN_TOKEN}"  # Assuming LOGIN_TOKEN is set in config
    }

    payload = [{
        "expense_date": datetime.strptime(expense_date, "%Y-%m-%d").isoformat() + "Z",
        "expense_type_id": expense_type_id,
        "farm_id": farm_id,
        "note": note,
        "value": value
    }]

    try:
        response = requests.post(
            f"{config.URL_LITEFARM}/expense/farm/{farm_id}",
            headers=headers,
            data=json.dumps(payload)
        )
        if response.status_code == 201:
            logging.info("Expense registered successfully")
            return response.json()
        else:
            logging.error(f"Error registering expense: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e: 
        logging.error(f"Request error: {e}") #Dont know why this exception is triggering
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
        logging.error(f"Request error: {e}")
        return None

# Request revenue types from LiteFarm API
async def request_revenue_types() -> Optional[List[Dict[str, Any]]]:
    """
    Request revenue types from the LiteFarm API.
    
    Returns:
        List of revenue types if successful, None if there was an error
    """

    # Return static JSON data for testing/development
    static_revenue_types = [
        {
            "revenue_type_id": 1,
            "revenue_name": "Crop Sale",
            "farm_id": None,
            "deleted": False,
            "revenue_translation_key": "CROP_SALE",
            "agriculture_associated": None,
            "crop_generated": True,
            "custom_description": None,
            "retired": False
        },
        {
            "revenue_type_id": 405,
            "revenue_name": "Otros",
            "farm_id": "bb8be50e-1261-11f0-8528-0242ac150003",
            "deleted": False,
            "revenue_translation_key": "OTROS",
            "agriculture_associated": None,
            "crop_generated": False,
            "custom_description": "Otros tipos de ingresos",
            "retired": False
        }
    ]
    return static_revenue_types
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
    # Return static JSON data for testing/development
    static_crop_varieties = [
        {
            "crop_variety_id": "d90979d4-373c-11f0-82ec-be0a3bb4732c",
            "crop_id": 310,
            "crop_variety_name": "Acacia amarilla",
            "farm_id": "5aa78ca8-3236-11f0-a33e-66ab45519382",
            "supplier": "",
            "lifecycle": "PERENNIAL",
            "compliance_file_url": "",
            "organic": None,
            "genetically_engineered": None,
            "searched": None,
            "crop_variety_photo_url": "https://litefarm.nyc3.cdn.digitaloceanspaces.com/default_crop/v2/default.webp",
            "treated": None,
            "hs_code_id": "4403",
            "crop_varietal": "",
            "crop_cultivar": ""
        },
        {
            "crop_variety_id": "e12345a1-374a-11f0-82ec-be0a3bb4732c",
            "crop_id": 312,
            "crop_variety_name": "Tomate",
            "farm_id": "5aa78ca8-3236-11f0-a33e-66ab45519382",
            "supplier": "",
            "lifecycle": "ANNUAL",
            "compliance_file_url": "",
            "organic": True,
            "genetically_engineered": False,
            "searched": None,
            "crop_variety_photo_url": "https://litefarm.nyc3.cdn.digitaloceanspaces.com/default_crop/v2/default.webp",
            "treated": False,
            "hs_code_id": "0702",
            "crop_varietal": "",
            "crop_cultivar": ""
        },
        {
            "crop_variety_id": "e12345a2-374a-11f0-82ec-be0a3bb4732c",
            "crop_id": 315,
            "crop_variety_name": "Maíz",
            "farm_id": "5aa78ca8-3236-11f0-a33e-66ab45519382",
            "supplier": "",
            "lifecycle": "ANNUAL",
            "compliance_file_url": "",
            "organic": False,
            "genetically_engineered": True,
            "searched": None,
            "crop_variety_photo_url": "https://litefarm.nyc3.cdn.digitaloceanspaces.com/default_crop/v2/default.webp",
            "treated": True,
            "hs_code_id": "1005",
            "crop_varietal": "Híbrido triple",
            "crop_cultivar": "Golden Sweet"
        },
        {
            "crop_variety_id": "e12345a3-374a-11f0-82ec-be0a3bb4732c",
            "crop_id": 318,
            "crop_variety_name": "Lechuga",
            "farm_id": "5aa78ca8-3236-11f0-a33e-66ab45519382",
            "supplier": "",
            "lifecycle": "ANNUAL",
            "compliance_file_url": "",
            "organic": True,
            "genetically_engineered": False,
            "searched": None,
            "crop_variety_photo_url": "https://litefarm.nyc3.cdn.digitaloceanspaces.com/default_crop/v2/default.webp",
            "treated": False,
            "hs_code_id": "0705",
            "crop_varietal": "",
            "crop_cultivar": "Butterhead"
        },
        {
            "crop_variety_id": "e12345a4-374a-11f0-82ec-be0a3bb4732c",
            "crop_id": 320,
            "crop_variety_name": "Cafe",
            "farm_id": "5aa78ca8-3236-11f0-a33e-66ab45519382",
            "supplier": "",
            "lifecycle": "PERENNIAL",
            "compliance_file_url": "",
            "organic": None,
            "genetically_engineered": None,
            "searched": None,
            "crop_variety_photo_url": "https://litefarm.nyc3.cdn.digitaloceanspaces.com/default_crop/v2/default.webp",
            "treated": None,
            "hs_code_id": "0901",
            "crop_varietal": "Typica",
            "crop_cultivar": "Bourbon"
        }
    ]
    return static_crop_varieties

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