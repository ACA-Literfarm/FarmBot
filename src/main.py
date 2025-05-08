import os
import asyncio
import logging
import sys
import json
from prompts import FINANCIAL_CLASSIFIER_PROMPT
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from openai import AsyncOpenAI
from typing import cast
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

load_dotenv()

# Set your bot and AI token here or use an environment variable
BOT_TOKEN = os.getenv("TELEGRAM_API_KEY")

if not BOT_TOKEN:
    raise ValueError("Please set the TELEGRAM_API_KEY environment variable.")

AI_API_KEY = os.getenv("AI_API_KEY")

if not AI_API_KEY:
    raise ValueError("Please set the AI_API_KEY environment variable.")

MODEL_NAME = os.getenv("MODEL_NAME")

if not MODEL_NAME:
    raise ValueError("Please set the MODEL_NAME environment variable.")

if FINANCIAL_CLASSIFIER_PROMPT is None:
    raise ValueError("Please set the FINANCIAL_CLASSIFIER_PROMPT environment variable.")

client = AsyncOpenAI(
    api_key=AI_API_KEY,
    #base_url="https://api.deepseek.com", # Uncomment if using Deepseek
)

# Initialize the bot and dispatcher
dp = Dispatcher()

# --- Deepseek consulting function ---
async def query_ai_model(user_message: str) -> str:
    try:

        messages = [
            {"role": "system", "content": FINANCIAL_CLASSIFIER_PROMPT},
            {"role": "user", "content": user_message},
        ]

        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=100,
            temperature=0.3,
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
        "Save transaction - ..."  #Show instructions for saving transaction
    )
    await message.answer(help_text)

@dp.message()
async def handle_regular_message(message: Message):
    if message.text.startswith('/'):
        return

    user_input = message.text.strip()
    response_text = await query_ai_model(user_input)

    try:
        data = json.loads(response_text)

        clasificacion = data.get("clasificacion")
        respuesta = data.get("respuesta")

        if not clasificacion or not respuesta:
            raise ValueError("Missing expected keys in AI response.")
        
        if clasificacion == "no_relacionado":
            respuesta += "\n\nℹ️ Si necesitas ayuda, escribe /help para ver los comandos disponibles."

        await message.answer(respuesta)

    except json.JSONDecodeError:
        logging.warning("Respuesta del modelo no tiene formato JSON válido.")
        await message.answer("❌ Lo siento, no entendí tu mensaje. ¿Podrías reformularlo?")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())