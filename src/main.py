import os
import asyncio
import logging
import sys
import json
from prompts import FINANCIAL_CLASSIFIER_PROMPT
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher 
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command 
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

# --- LiteFarmAPI consulting function ---
async def handle_api_transaction(api_response: json):
    
    note = api_response.get("note")
    value = api_response.get("value")
    type_ = api_response.get("type")

    logging.info(f"API Transaction: Note: {note}, Value: {value}, Type: {type_}")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("👋 ¡Bienvenido a LiteFarmBot! Usa /help para ver los comandos disponibles.")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "🤖 Comandos disponibles:\n"
        "/start - Mensaje de bienvenida\n"
        "/help - Mostrar este mensaje de ayuda\n\n"
        "📋 Ejemplos de uso:\n"
        "• Para registrar compras: 'Hoy gasté 50 dólares en un 20 bolsas de fertilizante'\n"
        "• Para registrar ingresos: 'Hoy vendí 30 dólares de un paquete de 120 manzanas'\n"
    )
    await message.answer(help_text)

# Diccionario para rastrear el estado del usuario
user_states = {}

@dp.message()
async def handle_regular_message(message: Message):
    user_id = message.from_user.id  # Identificar al usuario por su ID
    user_input = message.text.strip()

    # Verificar si el usuario está completando un campo faltante
    if user_id in user_states:
        state = user_states[user_id]
        missing_field = state["missing_fields"].pop(0)  # Obtener el siguiente campo faltante
        state["api_response"][missing_field] = user_input  # Guardar el valor proporcionado

        # Si aún faltan campos, solicitar el siguiente
        if state["missing_fields"]:
            next_field = state["missing_fields"][0]
            await message.answer(f"Por favor, proporciona el valor para '{next_field}':")
            return
        else:
            # Todos los campos están completos
            api_response = state["api_response"]
            del user_states[user_id]  # Limpiar el estado del usuario
            await handle_api_transaction(api_response)
            await message.answer(state["respuesta"])  # Responder con el mensaje original de la IA
            return

    # Si no hay estado previo, procesar el mensaje normalmente
    if not user_input:
        await message.answer("⚠️ El mensaje está vacío. Por favor, escribe algo para que pueda ayudarte.")
        return

    response_text = await query_ai_model(user_input)

    try:
        data = json.loads(response_text)

        clasificacion = data.get("clasificacion")
        respuesta = data.get("respuesta")
        api_response = data.get("respuesta_api", {"note": "", "value": "", "type": ""})

        if clasificacion == "no_relacionado":
            respuesta += "\n\nℹ️ Si necesitas ayuda, escribe /help para ver los comandos disponibles y ejemplos de uso."
            await message.answer(respuesta)
            return  # Salir sin completar datos

        # Verificar si faltan campos en la respuesta de la IA
        missing_fields = []
        if not api_response.get("note"):
            missing_fields.append("note")
        if not api_response.get("value"):
            missing_fields.append("value")
        if not api_response.get("type"):
            missing_fields.append("type")

        if missing_fields:
            # Guardar el estado del usuario
            user_states[user_id] = {
                "missing_fields": missing_fields,
                "api_response": api_response,
                "respuesta": respuesta,
            }
            await message.answer(
                f"⚠️ Faltaron datos para completar la transacción.\n"
                f"Por favor, proporciona el valor para '{missing_fields[0]}':"
            )
            return

        # Manejar la respuesta de la API
        await handle_api_transaction(api_response)
        await message.answer(respuesta)

    except json.JSONDecodeError:
        logging.warning("Respuesta del modelo no tiene formato JSON válido. Respuesta recibida: %s", response_text)
        await message.answer(
            "❌ Lo siento, no entendí tu mensaje o hubo un error procesando la respuesta. "
            "Por favor, intenta reformular tu mensaje o usa /help para ver ejemplos de uso."
        )


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())