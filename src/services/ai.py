import logging
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from prompts.financial import FINANCIAL_CLASSIFIER_PROMPT
from config import AI_API_KEY, MODEL_NAME

client = AsyncOpenAI(api_key=AI_API_KEY)

async def query_ai_model(user_message: str) -> str:
    try:
        messages = [
            ChatCompletionSystemMessageParam(role="system", content=FINANCIAL_CLASSIFIER_PROMPT),
            ChatCompletionUserMessageParam(role="user", content=user_message),
        ]
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