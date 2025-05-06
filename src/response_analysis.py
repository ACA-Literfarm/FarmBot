import os
import asyncio
import logging
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from openai import AsyncOpenAI
import re

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables with error handling
BOT_TOKEN = os.getenv("TELEGRAM_API_KEY")
if not BOT_TOKEN:
    raise ValueError("Please set the TELEGRAM_API_KEY environment variable.")

AI_API_KEY = os.getenv("AI_API_KEY")
if not AI_API_KEY:
    raise ValueError("Please set the AI_API_KEY environment variable.")

# Initialize OpenAI client for API calls
client = AsyncOpenAI(
    api_key=AI_API_KEY,
    # base_url="https://api.deepseek.com", # Uncomment if using Deepseek models instead of OpenAI
)

# Initialize memory storage for maintaining conversation state across messages
storage = MemoryStorage()
# Create dispatcher with storage for handling updates from Telegram
dp = Dispatcher(storage=storage)

# System prompt for the AI financial assistant
FINANCIAL_CLASSIFIER_PROMPT = """
Role: You are a financial assistant for a farm management application. You must converse with the user, help identify expenses or income from their farm business, and record incomplete records with up to three consecutive tolerance messages to fill in missing fields. Always respond in Spanish in a way that is understandable to a non-technical user. Keep in mind that the conversation may be very colloquial. Use emojis when possible.
Rules:
1. Message Types:
- EXPENSE: Costs ("I paid $50 for seeds")
- INCOME: Income ("I sold milk for $200")
- UNRELATED: No financial context
2. Required Fields (for complete records):
- Amount (numeric, always assume US dollars).
- Reason for the transaction (product, service provided, utility expense, etc.).
- Notes (not required; if a currency other than US dollars was used, record the exchange rate).
- Date (if not specified, assume the day the message was logged).
3. Memory Management:
- Remember incomplete records for 3 messages.
- Reset context after 3 messages of an incomplete register process or if the user starts a new record. Politely indicate context reset.
- Display the remaining missing fields in each follow-up
4. Atomic responses:
- COMPLETE: "Recorded [type (expense/income)]: [amount] for [reason] ([date], [notes])"
- MISSING: "[Fields] are missing for [partial information]. Example: '[field]: value'"
- ERROR: "Error: [reason] (mixed types/unclear)"
- UNRELATED: "No financial action"
- MEMORY INFORMATION: "[Fields] are still missing for your [partial record]"
- TIMEOUT: When 3 messages pass without completing a record, include "TIMEOUT" in your response and explain that the record attempt has been canceled

When the user says things like “hoy”, “ayer”, “5 de mayo”, or “el 3”, you must extract the date and convert it to ISO format yyyy-mm-dd.
Always assume the current year unless specified. Assume “hoy” is the day of the message. If the user says “ayer”, subtract one day.
Update the "date" field in the record accordingly, and remove it from missing_fields if it’s now filled.

Contextual Memory:
You will always receive the user's message followed by a JSON block called "Current state data".
This contains the current memory about the financial record, including:
- type: "INCOME" or "EXPENSE"
- record: a dict of collected fields (amount, reason, notes, date)
- missing_fields: which required fields are still needed
- message_count: how many messages have passed in the current registration attempt

You must treat this as memory from the previous conversation. Use it to:
- Fill in missing fields if the user provides them later.
- Track if the record is now complete.
- Reset memory if 3 messages have passed (`message_count` > 3).
- Include a "state_update" JSON block in your response like this:

{
  "type": "EXPENSE",
  "record": {"amount": 50, "reason": "semillas"},
  "missing_fields": ["date"],
  "has_financial_info": true
}

Always include that block inside your message (at the end) so the system can extract updated state. Always include all keys, even if empty.
"""


# Function to process user messages with the AI financial classifier
async def query_financial_classifier(user_message: str, state_data: dict) -> dict:
    """
    Sends the user message and current state to the AI model for classification and processing.

    Args:
        user_message: The text message from the user
        state_data: Dictionary containing the current conversation state

    Returns:
        The AI's response text
    """
    context_message = f"{user_message}\n\nCurrent state data: {json.dumps(state_data)}"

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": FINANCIAL_CLASSIFIER_PROMPT},
                {"role": "user", "content": context_message},
            ],
            max_tokens=300,
            temperature=0.3,
        )

        content = response.choices[0].message.content

        # Try to extract a JSON block from the AI's response (optional: make more robust)
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        state_update = json.loads(json_match.group()) if json_match else {}

        return {
            "reply": content,
            "state_update": state_update
        }

    except Exception as e:
        logging.error(f"Error AI: {e}")
        return {
            "reply": "⚠️ Hubo un error procesando tu mensaje. Intenta de nuevo más tarde.",
            "state_update": {}
        }

# Handler for the /start command - initializes the conversation
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Handles the /start command, resets state and sends welcome message.

    Args:
        message: The Telegram message object
        state: The FSM context for state management
    """
    # Clear any existing conversation state
    await state.clear()
    # Send welcome message with introduction
    await message.answer("👋 Bienvenido a FarmBot Financiero! Usa /help para ver los comandos disponibles.")


# Handler for the /help command - shows available commands and examples
@dp.message(Command("help"))
async def cmd_help(message: Message):
    """
    Responds to the /help command with usage instructions and examples.

    Args:
        message: The Telegram message object
    """
    help_text = (
        "🤖 Comandos disponibles:\n"
        "/start - Mensaje de bienvenida\n"
        "/help - Mostrar este mensaje de ayuda\n"
        "/reset - Reiniciar la conversación financiera actual\n\n"
        "Ejemplos de transacciones:\n"
        "- \"Vendí zanahorias por $200\"\n"
        "- \"Pagué $50 por semillas\"\n"
        "- \"Compré equipo por $1000 hoy\""
    )
    await message.answer(help_text)


# Handler for the /reset command - manually clears the conversation state
@dp.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    """
    Handles the /reset command, clears the current financial conversation state.

    Args:
        message: The Telegram message object
        state: The FSM context for state management
    """
    # Clear the conversation state
    await state.clear()
    # Confirm reset to the user
    await message.answer("✅ He reiniciado tu conversación financiera. Puedes comenzar un nuevo registro.")


# Handler for all regular (non-command) messages
@dp.message()
async def handle_financial_message(message: Message, state: FSMContext):
    """
    Processes regular text messages for financial classification and tracking.
    Maintains conversation state across multiple messages to collect all required fields.

    Args:
        message: The Telegram message object
        state: The FSM context for state management
    """
    # Skip processing for unregistered commands (starting with '/')
    if message.text.startswith('/'):
        return

    # Retrieve current conversation state
    state_data = await state.get_data()

    # Initialize state if this is a new conversation
    if not state_data:
        state_data = {
            "message_count": 0,  # Counter for consecutive messages in a financial context
            "record": {},  # Stores the financial record data
            "type": None,  # Type of transaction (EXPENSE/INCOME)
            "missing_fields": [],  # List of fields still needed
            "has_financial_info": False  # Flag to track if we've detected financial info
        }

    # Process the message with the AI financial classifier
    result = await query_financial_classifier(message.text, state_data)
    ai_response = result["reply"]
    update = result.get("state_update", {})

    # Merge updates into FSM state if any
    if update:
        state_data.update(update)
        await state.update_data(**state_data)

    # First, check if this is a financial message by looking at the response
    is_financial_message = (
            "MISSING" in ai_response or
            "MEMORY INFORMATION" in ai_response or
            "COMPLETE" in ai_response or
            "ERROR" in ai_response
    )

    # Update state based on AI response type
    if "COMPLETE" in ai_response:
        # Record is complete - reset state and respond
        await state.clear()
        await message.answer(ai_response)

    elif "UNRELATED" in ai_response:
        # Message is not related to finances
        if state_data.get("has_financial_info") and state_data.get("missing_fields"):
            # We have an ongoing financial record, notify about context switch
            await message.answer("💬 Estoy cambiando de tema. El registro financiero anterior quedará pendiente.")
        # Reset the state since it's not financial
        await state.clear()
        # Respond to the unrelated message
        await message.answer(ai_response)

    elif "MISSING" in ai_response or "MEMORY INFORMATION" in ai_response:
        # This is a financial message with missing fields

        # If this is the first financial message or a new record after completion,
        # initialize the state properly
        if not state_data.get("has_financial_info"):
            state_data["has_financial_info"] = True
            state_data["message_count"] = 1
        else:
            # Increment the message counter for existing financial conversations
            state_data["message_count"] += 1

        # Check if we've hit the 3-message limit for incomplete records
        if state_data["message_count"] > 3:
            # We've exceeded the limit, inform the user and reset
            timeout_message = "⏰ Han pasado 3 mensajes sin completar el registro financiero. Vamos a reiniciar. Si deseas registrar una transacción, por favor intenta de nuevo con todos los detalles necesarios. ¡Gracias!"
            await message.answer(timeout_message)
            # Reset the state
            await state.clear()
            # Add a friendly greeting to restart the conversation
            await message.answer("👋 ¿En qué más puedo ayudarte hoy?")
        else:
            # Still within the 3-message limit, update state and continue
            await state.update_data(
                message_count=state_data["message_count"],
                has_financial_info=True
            )
            await message.answer(ai_response)

    elif "ERROR" in ai_response:
        # For error responses, just respond without changing state tracking
        await message.answer(ai_response)

    else:
        # For any other type of response
        await message.answer(ai_response)


# Main function to start the bot
async def main() -> None:
    """
    Initializes the bot and starts polling for updates.
    """
    # Create a bot instance with HTML parsing
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Start listening for updates from Telegram
    await dp.start_polling(bot)


# Entry point of the script
if __name__ == "__main__":
    # Configure logging to see informational messages
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    # Run the main function
    asyncio.run(main())