import logging
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from prompts.financial import generate_financial_prompt
from config import AI_API_KEY, MODEL_NAME
from services.api import get_revenue_types

client = AsyncOpenAI(api_key=AI_API_KEY)

"""
Queries the AI model with a dynamically generated financial assistant prompt.

Args:
    user_message (str): The user's input message.
    farm_id (str): The farm ID for context.
    token (str): The authorization token for API requests.
    include_revenue_types (bool): Whether to include revenue types in the prompt.
    revenue_types (list[str]): A list of revenue type names.
    include_crop_varieties (bool): Whether to include crop varieties in the prompt.
    crop_varieties (list[str]): A list of crop variety names.

Returns:
    str: The AI model's response.
"""
from typing import Optional

async def query_ai_model(user_message: str,
                         revenue_types: Optional[list[str]] = None,
                         crop_varieties: Optional[list[str]] = None) -> str:
    try:
        # Generate the system prompt dynamically
        system_prompt = generate_financial_prompt(
            revenue_types=revenue_types,
            crop_varieties=crop_varieties
        )

        # Prepare the messages for the AI model
        messages = [
            ChatCompletionSystemMessageParam(role="system", content=system_prompt),
            ChatCompletionUserMessageParam(role="user", content=user_message),
        ]

        # Query the AI model
        response = await client.chat.completions.create(
            model=str(MODEL_NAME),
            messages=messages,
            max_tokens=100,
            temperature=0.3,
        )
        return response.choices[0].message.content or "No response generated"
    except Exception as e:
        logging.error(f"Error querying AI model: {e}")
        return "⚠️ There was an error processing your message. Try again later."