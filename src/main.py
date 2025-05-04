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

# --- Deepseek consulting function ---
async def query_deepseek(user_message: str) -> str:
    try:
        response = await client.chat.completions.create(
            #model="deepseek-chat", # Uncomment if using Deepseek
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Responde en 1-2 frases cortas. Eres un bot para pruebas de desarrollo.
                Ejemplo: Soy un bot. No gasto muchos tokens"""},
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
