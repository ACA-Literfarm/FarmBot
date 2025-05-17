import json
import logging
from aiogram.types import Message
from bot.state import user_states
from services.ai import query_ai_model
from services.api import handle_api_transaction

async def handle_regular_message(message: Message):
    if message.from_user is None:
        await message.answer("⚠️ No se pudo identificar al usuario. Por favor, intenta nuevamente.")
        return

    user_id = message.from_user.id
    user_input = message.text.strip() if message.text else ""

    # Verificar si el usuario está completando un campo faltante
    if user_id in user_states:
        state = user_states[user_id]
        missing_field = state["missing_fields"].pop(0)  # Obtener el siguiente campo faltante
        state["api_response"][missing_field] = user_input  # Guardar el valor proporcionado

        # Si aún faltan campos, solicitar el siguiente
        if state["missing_fields"]:
            next_field = state["missing_fields"][0]
            if next_field == "value":
                await message.answer("💰 Por favor, ingresa el precio de la transacción:")
            elif next_field == "note":
                await message.answer("📝 Por favor, proporciona una breve descripción de la transacción:")
            elif next_field == "type":
                await message.answer("📂 Por favor, indica el tipo de transacción (por ejemplo: gasolina, maquinaria, plantas, otro):")
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
            first_missing_field = missing_fields[0]
            if first_missing_field == "value":
                await message.answer("💰 Faltó el precio de la transacción. Por favor, ingrésalo:")
            elif first_missing_field == "note":
                await message.answer("📝 Faltó la descripción de la transacción. Por favor, proporciónala:")
            elif first_missing_field == "type":
                await message.answer("📂 Faltó el tipo de transacción. Por favor, indícalo (por ejemplo: gasolina, maquinaria, plantas, otro):")
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