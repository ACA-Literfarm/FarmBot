import json
import logging
from aiogram.types import Message
from services.ai_service import query_ai_model
from services.api_service import handle_api_transaction, request_expense_types

# Diccionario para rastrear el estado del usuario
user_states = {}

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

    # Request expense types from litefarm API 
    expense_type = await request_expense_types()

    # Check if there was an error getting expense types
    if expense_type is None:
        await message.answer("Hubo un error en el servidor obteninendo tipos de gastos, intentalo mas tarde.")
        return

    # Query the AI model with the user's input and available expense types
    response_text = await query_ai_model(user_input, expense_type)

    try:
        data = json.loads(response_text)

        clasificacion = data.get("clasificacion")
        respuesta = data.get("respuesta")
        api_response = data.get("respuesta_api", {"note": "", "value": "", "type": ""})

        # When an expense is detected, show available expense types
        # What it does: Based on the list of expense types, it formats them for user display.
        # This will also show the selected expense type if it exists in the response.
        if clasificacion == "gasto":
            # Format expense types for user display
            expense_options = []
            if expense_type:
                for item in expense_type:
                    if isinstance(item, dict):
                        expense_id = item.get('expense_type_id', '')
                        name = item.get('expense_name', '')
                        if expense_id and name:
                            expense_options.append(f"• {name}")

            # If there are expense options, include them in the response
            if expense_options and api_response.get("type"):
                selected_type = api_response.get("type")
                selected_name = ""

                # Find the name of the selected expense type
                for item in expense_type:
                    if isinstance(item, dict) and str(item.get('expense_type_id', '')) == str(selected_type):
                        selected_name = item.get('expense_name', '')
                        break

                if not selected_name and selected_type:
                    # If we couldn't find the ID in the list, maybe the AI sent the name directly
                    selected_name = selected_type

                # Prepare the list of expense options
                expense_list = "\n".join(expense_options)
                respuesta = f"De los siguientes tipos de gastos:\n\n{expense_list}\n\nSeleccioné este tipo: {selected_name}\n\n{respuesta}"
            else:
                respuesta = "No pude identificar un tipo de gasto específico. Por favor, asegúrate de que el mensaje incluya un tipo de gasto válido.\n\n" + respuesta

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