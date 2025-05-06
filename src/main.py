import os
import asyncio
import logging
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from openai import AsyncOpenAI

load_dotenv()

# Set your bot and AI token here or use an environment variable
BOT_TOKEN = os.getenv("TELEGRAM_API_KEY")
if not BOT_TOKEN:
    raise ValueError("Please set the TELEGRAM_API_KEY environment variable.")

AI_API_KEY = os.getenv("AI_API_KEY")
if not AI_API_KEY:
    raise ValueError("Please set the AI_API_KEY environment variable.")

client = AsyncOpenAI(
    api_key=AI_API_KEY, 
    #base_url="https://api.deepseek.com", # Uncomment if using Deepseek
)

# Initialize the bot and dispatcher
dp = Dispatcher()

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
"""

# Ignore for now
"""
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

# --- Deepseek consulting function ---
async def query_deepseek(user_message: str) -> str:
    try:
        response = await client.chat.completions.create(
            #model="deepseek-chat", # Uncomment if using Deepseek
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": FINANCIAL_CLASSIFIER_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=25, # Limit the response length
            temperature=0.3, # Increase for more creative responses (0.7)
        )
        return response.choices[0].message.content

    except Exception as e:
        logging.error(f"Error AI: {e}")
        return "⚠️ There was an error processing your message. Try again later."

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("👋 Welcome to LiteFarmBot! Use /help to see available commands.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "🤖 Available commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "Save transaction - ..." #Show instructions for saving transaction
    )
    await message.answer(help_text)

# --- Handler for regular messages ---
@dp.message()
async def handle_regular_message(message: Message):
    if message.text.startswith('/'):  # Ignores not registered commands
        return

    response = await query_deepseek(message.text)
    await message.answer(response)

async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
