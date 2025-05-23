import json
import logging
from aiogram.types import Message
from bot.state import user_states
from services.ai import query_ai_model
from services.api import handle_api_transaction, get_revenue_types
from cache import crop_cache
from config import LOGIN_TOKEN, FARM_ID

async def handle_regular_message(message: Message):
    if message.from_user is None:
        await message.answer("⚠️ No se pudo identificar al usuario. Por favor, intenta nuevamente.")
        return

    user_id = message.from_user.id

    # Burned values for now (replace with dynamic values later)
    farm_id = str(FARM_ID)  # Replace with dynamic farm_id
    token = str(LOGIN_TOKEN)  # Replace with dynamic token

    user_input = message.text.strip() if message.text else ""

    if not user_input:
        await message.answer("⚠️ El mensaje está vacío. Por favor, escribe algo para que pueda ayudarte.")
        return

    response_text = ""  # Initialize response_text to avoid unbound variable error
    try:
        # Step 1: Get crop varieties from cache (optimized)
        crop_varieties_result = await crop_cache.get_crop_varieties(farm_id, token)
        if not crop_varieties_result["success"]:
            await message.answer("⚠️ Error al obtener las variedades de cultivos. Por favor, intenta nuevamente más tarde.")
            return

        crop_varieties = [item["crop_variety_name"] for item in crop_varieties_result["data"]]

        # Generate a generic crop varieties list for the AI model if list is empty
        if not crop_varieties or len(crop_varieties) == 0:
            logging.warning("No se encontraron variedades de cultivos. Usando lista genérica.")
            crop_varieties = ["maíz", "trigo", "soja", "arroz", "cebada", "sorgo", "mijo", "avena"]

        # Log cache usage
        from_cache = crop_varieties_result.get("from_cache", False)
        cache_status = "caché" if from_cache else "API"

        # Query the AI model with crop varieties included
        response_text = await query_ai_model(
            user_message=user_input,
            crop_varieties=crop_varieties,
        )

        data = json.loads(response_text)

        clasificacion = data.get("clasificacion")
        respuesta = data.get("respuesta")
        api_response = data.get("respuesta_api", {"note": "", "value": "", "type": ""})

        if clasificacion == "no_relacionado":
            respuesta += "\n\nℹ️ Si necesitas ayuda, escribe /help para ver los comandos disponibles y ejemplos de uso."
            await message.answer(respuesta)
            return  # Exit without further processing

        # Step 2: If classified as "ingreso," fetch revenue types and re-query the AI model
        if clasificacion == "ingreso":
            
            # Initialize revenue_types to avoid unbound variable error
            revenue_types = []
            
            # Fetch revenue types (consider adding cache for this too)
            revenue_types_result = await get_revenue_types(farm_id, token)

            if not revenue_types_result["success"]:
                await message.answer("⚠️ Error al obtener los tipos de ingresos. Por favor, intenta nuevamente más tarde.")
                return

            revenue_types = [item["revenue_name"].lower() for item in revenue_types_result["data"]]

            # Re-query the AI model with revenue types included
            response_text = await query_ai_model(
                user_message=user_input,
                revenue_types=revenue_types,
                crop_varieties=crop_varieties
            )

            data = json.loads(response_text)
            respuesta = data.get("respuesta")
            api_response = data.get("respuesta_api", {"note": "", "value": "", "type": ""})

            # Step 3: Validate crop variety if the transaction involves crops
            if api_response.get("type") and api_response["type"] in revenue_types:
                # Check if the identified crop variety is in the list
                identified_crop = api_response["note"]
                crop_varieties_lower = [crop.lower() for crop in crop_varieties]
                
                # Extract potential crop names from the identified_crop string
                identified_crop_words = identified_crop.lower().split()
                crop_found = False
                
                # Check if any crop variety matches or is contained in the identified_crop
                for crop in crop_varieties_lower:
                    crop_words = crop.split()
                    # Check if all words of the crop variety are in the identified_crop
                    if all(word in identified_crop_words for word in crop_words):
                        crop_found = True
                        break
                
                if not crop_found:
                    # Crop variety not found in the list
                    available_crops = ", ".join(crop_varieties[:10])  # Show first 10 varieties
                    if len(crop_varieties) > 10:
                        available_crops += f" (y {len(crop_varieties) - 10} más)"
                    
                    await message.answer(
                        f"❌ La variedad de cultivo '{identified_crop}' no está registrada en tu granja.\n\n"
                        f"🌱 Variedades disponibles: {available_crops}\n\n"
                        f"Por favor, reformula tu mensaje usando una de las variedades disponibles o usa /crop_varieties para ver la lista completa."
                    )
                    return  # Exit without registering the transaction
            else:
                await message.answer(
                    "❌ El tipo de movimiento que especificaste no se encuentra contemplado. Puedes usar /revenue_types para ver los tipos de ingresos disponibles.\n\n"
                )
                return

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