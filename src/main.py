import os
import asyncio
import logging
import sys
import json

sys.path.append(os.path.dirname(__file__))  # Añade el path actual (donde está main.py)
from prompts import FINANCIAL_CLASSIFIER_PROMPT
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from openai import AsyncOpenAI

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_API_KEY")
AI_API_KEY = os.getenv("AI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

if not BOT_TOKEN:
    raise ValueError("Please set the TELEGRAM_API_KEY environment variable.")

if not AI_API_KEY:
    raise ValueError("Please set the AI_API_KEY environment variable.")

if not MODEL_NAME:
    raise ValueError("Please set the MODEL_NAME environment variable.")

if FINANCIAL_CLASSIFIER_PROMPT is None:
    raise ValueError("Please set the FINANCIAL_CLASSIFIER_PROMPT environment variable.")

client = AsyncOpenAI(api_key=AI_API_KEY)

dp = Dispatcher()

# --- Función para consultar al modelo AI ---
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

        # Soporte para pruebas (dict) o respuesta real (objeto)
        if isinstance(response, dict):
            content = response["choices"][0]["message"]["content"]
        else:
            content = response.choices[0].message.content

        return content

    except Exception as e:
        logging.error(f"Error AI: {e}")
        return "⚠️ There was an error processing your message. Try again later."

# --- Función para manejar transacción API simulada ---
async def handle_api_transaction(api_response: json):
    note = api_response.get("note")
    value = api_response.get("value")
    type_ = api_response.get("type")

    logging.info(f"API Transaction: Note: {note}, Value: {value}, Type: {type_}")

# --- Comandos Telegram ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("👋 ¡Bienvenido a LiteFarmBot! Usa /help para ver los comandos disponibles.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "🤖 Comandos disponibles:\n"
        "/start - Mensaje de bienvenida\n"
        "/help - Mostrar este mensaje de ayuda\n"
    )
    await message.answer(help_text)

# --- Manejo de mensajes comunes ---
@dp.message()
async def handle_regular_message(message: Message):
    if message.text.startswith('/'):
        return

    user_input = message.text.strip()
    if not user_input:
        await message.answer("⚠️ El mensaje está vacío. Por favor, escribe algo para que pueda ayudarte.")
        return

    response_text = await query_ai_model(user_input)

    try:
        data = json.loads(response_text)

        clasificacion = data.get("clasificacion")
        respuesta = data.get("respuesta")
        api_response = data.get("respuesta_api", {"note": "", "value": "", "type": ""})

        if not clasificacion or not respuesta:
            raise ValueError("Faltan claves esperadas en la respuesta de la IA.")

        if clasificacion == "no_relacionado":
            respuesta += "\n\nℹ️ Si necesitas ayuda, escribe /help para ver los comandos disponibles."

        await handle_api_transaction(api_response)
        await message.answer(respuesta)

    except json.JSONDecodeError:
        logging.warning("Respuesta del modelo no tiene formato JSON válido. Respuesta recibida: %s", response_text)
        await message.answer(
            "❌ Lo siento, no entendí tu mensaje o hubo un error procesando la respuesta. "
            "Por favor, intenta reformular tu mensaje o usa /help para ver ejemplos de uso."
        )

# --- Main ---
async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
