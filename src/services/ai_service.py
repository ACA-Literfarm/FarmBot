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

async def query_ai_model(user_message: str, expense_type: List[Dict[str, Any]]) -> str:
    """
    Query the AI model to classify and process user messages related to financial transactions.
    
    Args:
        user_message: The user's input message
        expense_type: List of available expense types from the API
        
    Returns:
        AI model response as a string (JSON format expected)
    """
    try:
        # Format expense types to be more readable for the AI
        formatted_expense_types = []
        if expense_type:
            for item in expense_type:
                if isinstance(item, dict):
                    expense_id = item.get('expense_type_id', '')
                    name = item.get('expense_name', '')
                    if expense_id and name:
                        formatted_expense_types.append(f"{expense_id}: {name}")

        expense_context = "Expense types available:\n" + "\n".join(formatted_expense_types) if formatted_expense_types else "No expense types available"

        messages = [
            {"role": "system", "content": FINANCIAL_CLASSIFIER_PROMPT},
            {"role": "system", "content": expense_context},
            {"role": "system", "content": "When user reports an expense, select the most appropriate expense type ID from the list above."},
            {"role": "user", "content": user_message},
        ]

        response = await client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=messages,
            max_tokens=150,
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:
        logging.error(f"Error AI: {e}")
        return "⚠️ There was an error processing your message. Try again later."


