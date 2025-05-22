import logging
import httpx

async def handle_api_transaction(api_response: dict):
    """
    Simulates handling an API transaction for financial records.
    Replace this with actual API calls to save data.
    """
    note = api_response.get("note")
    value = api_response.get("value")
    type_ = api_response.get("type")

    # Simulate saving to a database or external API
    logging.info(f"API TRANSACTION: Note: {note}, Value: {value}, Type: {type_}")
    # Add actual API call logic here

async def get_revenue_types(farm_id: str, token: str) -> dict:
    """
    Fetches the list of revenue types for a given farm.
    """
    try:
        # Prepare the URL
        url = f"http://localhost:5001/revenue_type/farm/{farm_id}"

        # Prepare the headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en",
            "farm_id": farm_id,
            "Authorization": f"Bearer {token}"
        }

        # Send the GET request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            return {"success": True, "data": data}
        else:
            logging.error(f"Failed to fetch revenue types: {response.text}")
            return {"success": False, "error": response.text}

    except Exception as e:
        logging.error(f"Error fetching revenue types: {e}")
        return {"success": False, "error": "An error occurred while fetching revenue types."}

async def get_crop_varieties(farm_id: str, token: str) -> dict:
    """
    Fetches the list of crop varieties for a given farm.
    """
    try:
        # Prepare the URL
        url = f"http://localhost:5001/crop_variety/farm/{farm_id}"

        # Prepare the headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en",
            "farm_id": farm_id,
            "Authorization": f"Bearer {token}"
        }

        # Send the GET request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Crop varieties fetched successfully for farm {farm_id}.")
            return {"success": True, "data": data}
        else:
            logging.error(f"Failed to fetch crop varieties: {response.text}")
            return {"success": False, "error": response.text}

    except Exception as e:
        logging.error(f"Error fetching crop varieties: {e}")
        return {"success": False, "error": "An error occurred while fetching crop varieties."}