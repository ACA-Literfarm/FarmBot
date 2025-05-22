import json
import logging
from aiogram.types import Message
from bot.state import user_states
from services.ai import query_ai_model
from services.api import handle_api_transaction, get_revenue_types
from config import LOGIN_TOKEN

async def handle_regular_message(message: Message):
    if message.from_user is None:
        await message.answer("⚠️ No se pudo identificar al usuario. Por favor, intenta nuevamente.")
        return

    user_id = message.from_user.id

    # Burned values for now (replace with dynamic values later)
    farm_id = "5aa78ca8-3236-11f0-a33e-66ab45519382"  # Replace with dynamic farm_id
    token = LOGIN_TOKEN  # Replace with dynamic token

    user_input = message.text.strip() if message.text else ""

    if not user_input:
        await message.answer("⚠️ El mensaje está vacío. Por favor, escribe algo para que pueda ayudarte.")
        return

    # Step 1: Query the AI model without revenue types
    response_text = await query_ai_model(user_input, include_revenue_types=False)

    try:
        data = json.loads(response_text)

        clasificacion = data.get("clasificacion")
        respuesta = data.get("respuesta")
        api_response = data.get("respuesta_api", {"note": "", "value": "", "type": ""})

        if clasificacion == "no_relacionado":
            respuesta += "\n\nℹ️ Si necesitas ayuda, escribe /help para ver los comandos disponibles y ejemplos de uso."
            await message.answer(respuesta)
            return  # Exit without further processing

        # Step 2: If classified as "ingreso", fetch revenue types and re-query the AI model
        if clasificacion == "ingreso":

            # Fetch revenue types
            revenue_types_result = await get_revenue_types(farm_id, token)
 
            if not revenue_types_result["success"]:
                await message.answer("⚠️ Error al obtener los tipos de ingresos. Por favor, intenta nuevamente más tarde.")
                return

            revenue_types = [item["revenue_name"] for item in revenue_types_result["data"]]

            # Re-query the AI model with revenue types included
            response_text = await query_ai_model(
                user_message=user_input,
                farm_id=farm_id,
                token=token,
                include_revenue_types=True,
                revenue_types=revenue_types,
            )

            data = json.loads(response_text)
            respuesta = data.get("respuesta")
            api_response = data.get("respuesta_api", {"note": "", "value": "", "type": ""})

        # Check for missing fields in the API response
        missing_fields = []
        if not api_response.get("note"):
            missing_fields.append("note")
        if not api_response.get("value"):
            missing_fields.append("value")
        if not api_response.get("type"):
            missing_fields.append("type")

        if missing_fields:
            # Save the user's state for completing missing fields
            user_states[user_id] = {
                "missing_fields": missing_fields,
                "api_response": api_response,
                "respuesta": respuesta,
            }
            first_missing_field = missing_fields[0]
            if first_missing_field == "value":
                await message.answer("💰 Faltó el precio de la transacción. Por favor, ingrésalo:")
            elif first_missing_field == "note":
                await message.answer("📝 Faltó la descripción de la transacción. Por favor, proporciónala:")
            elif first_missing_field == "type":
                await message.answer("📂 Faltó el tipo de transacción. Por favor, indícalo (por ejemplo: gasolina, maquinaria, plantas, otro):")
            return

        # Handle the API transaction
        await handle_api_transaction(api_response)
        await message.answer(respuesta)

    except json.JSONDecodeError:
        logging.warning("Respuesta del modelo no tiene formato JSON válido. Respuesta recibida: %s", response_text)
        await message.answer(
            "❌ Lo siento, no entendí tu mensaje o hubo un error procesando la respuesta. "
            "Por favor, intenta reformular tu mensaje o usa /help para ver ejemplos de uso."
        )