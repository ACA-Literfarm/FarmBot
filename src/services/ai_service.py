from datetime import date
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from prompts import FINANCIAL_CLASSIFIER_PROMPT
from config import config

# Validate required environment variables
config.validate_required_vars()

# Initialize OpenAI client
client = AsyncOpenAI(
    api_key=config.AI_API_KEY,
    # base_url="https://api.deepseek.com", # Uncomment if using Deepseek
)

def format_expense_types_context(expense_types: List[Dict[str, Any]]) -> str:
    """Format expense types for AI context."""
    if not expense_types:
        return "No expense types available"
    
    formatted_types = []
    for item in expense_types:
        if isinstance(item, dict):
            expense_id = item.get('expense_type_id', '')
            name = item.get('expense_name', '')
            if expense_id and name:
                formatted_types.append(f"ID: {expense_id} - {name}")
    
    return "Expense types available:\n" + "\n".join(formatted_types) if formatted_types else "No expense types available"

def format_revenue_types_context(revenue_types: List[Dict[str, Any]]) -> str:
    """Format revenue types for AI context."""
    if not revenue_types:
        return "No revenue types available"
    
    formatted_types = []
    for item in revenue_types:
        if isinstance(item, dict):
            revenue_id = item.get('revenue_type_id', '')
            name = item.get('revenue_name', '')
            if revenue_id and name:
                formatted_types.append(f"ID: {revenue_id} - {name}")
    
    return "Revenue types available:\n" + "\n".join(formatted_types) if formatted_types else "No revenue types available"

def format_crop_varieties_context(crop_varieties: List[Dict[str, Any]]) -> str:
    """Format crop varieties for AI context."""
    if not crop_varieties:
        return "No crop varieties available"
    
    formatted_varieties = []
    for item in crop_varieties:
        if isinstance(item, dict):
            variety_id = item.get('crop_variety_id', '')
            name = item.get('crop_variety_name', '')
            crop_id = item.get('crop_id', '')
            if variety_id and name:
                # Include crop_id for additional context but prioritize variety_id and name
                formatted_varieties.append(f"ID: {variety_id} - {name}")
    
    return "Crop varieties available:\n" + "\n".join(formatted_varieties) if formatted_varieties else "No crop varieties available"

async def query_ai_model(user_message: str, expense_type: List[Dict[str, Any]], revenue_type: List[Dict[str, Any]], crop_variety: List[Dict[str, Any]]) -> str:
    """
    Query the AI model to classify and process user messages related to financial transactions.
    
    Args:
        user_message: The user's input message
        expense_type: List of available expense types from the API
        
    Returns:
        AI model response as a string (JSON format expected)
    """
    try:
        # Format contexts using helper functions
        expense_context = format_expense_types_context(expense_type)
        revenue_context = format_revenue_types_context(revenue_type)
        crop_variety_context = format_crop_varieties_context(crop_variety)
        # Today date in ISO format
        today_date = date.today().isoformat()

        # Prepare the context messages for the AI model to analyze.
        messages = [
            {"role": "system", "content": FINANCIAL_CLASSIFIER_PROMPT},
            {"role": "system", "content": expense_context},
            {"role": "system", "content": f"Today date: {today_date}"},
            {"role": "system", "content": "When user reports an expense, select the most appropriate expense type ID from the list above."},
            {"role": "system", "content": "If the user mentions a specific date, extract it and format it as YYYY-MM-DD. Common date formats include: 'el día DD/MM/YYYY', 'DD/MM/YYYY', 'hoy' (today), 'ayer' (yesterday). If no specific date is mentioned, leave the date field empty."},
            {"role": "system", "content": revenue_context},
            {"role": "system", "content": crop_variety_context},
            {"role": "user", "content": user_message},
        ]

        # Send the request to the AI model
        response = await client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=messages,
            max_tokens=150,
            temperature=0.3,  # Very low temperature for consistent behavior
        )

        # Return the AI's response content
        ai_response = response.choices[0].message.content
        return ai_response

    except Exception as e:
        logging.error(f"Error AI: {e}")
        return """
        {
            "clasificacion": "no_relacionado",
            "respuesta": "⚠️ Hubo un error procesando tu mensaje. Por favor, intenta nuevamente.",
            "respuesta_api": {
                "note": "",
                "value": "",
                "type": "",
                "date": "",
                "crop_variety": "",
                "customer": ""
            }
        }
        """


