import json
import logging
from datetime import datetime, date
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ChatAction
from services.ai_service import query_ai_model
from services.api_service import handle_api_transaction, request_expense_types, request_revenue_types, request_crop_varieties
from services.typing_context import show_typing
from commands.disable_validation import get_validation_enabled
from middleware.fields_validator import (
    validate_expense_fields, 
    validate_revenue_fields, 
    validate_revenue_type, 
    validate_crop_variety,
    validate_expense_type,
    validate_transaction_context,
    validate_field
)
from shared.DTO.farm.farm_dto import FarmDTO
from shared.services.farm_selection_service import FarmSelectionService
from shared.repositories.farm_repository import FarmRepository
from shared.repositories.chat_repository import ChatSessionRepository
from shared.db.session import AsyncSessionLocal
from shared.db.models.farm import Farm
from typing import Optional

import logging
import re

from shared.utils.number_utils import extract_numeric


logging.basicConfig(level=logging.INFO)
loggger = logging.getLogger(__name__)

farm_service = FarmSelectionService(
    repo_factory=FarmRepository,  # Replace with actual repository factory if needed
    chat_session_repo_factory=ChatSessionRepository  # Replace with actual chat session repository
)

# Diccionario para rastrear el estado del usuario
user_states = {}

def get_greeting_response() -> str:
    """
    Get a friendly greeting response explaining what the bot does.
    
    Returns:
        A greeting message explaining the bot's functionality
    """
    return """👋 ¡Hola! Soy tu asistente financiero agrícola 🤖

Te ayudo a gestionar las finanzas de tu granja de manera fácil y rápida. Puedo ayudarte con:

💰 **Registro de Gastos**: Fertilizantes, pesticidas, herramientas, mano de obra, etc.
💵 **Registro de Ingresos**: Ventas de cultivos, servicios agrícolas, etc.
📊 **Seguimiento**: Mantengo un registro organizado de todas tus transacciones

**¿Cómo funciona?**
Simplemente dime qué gasto o ingreso quieres registrar. Por ejemplo:
• "Compré fertilizante por $50"
• "Vendí tomates por $200 a Juan"
• "Pagué $100 por mano de obra"

**Comandos útiles:**
/selectfarm - Seleccionar granja
/currentfarm - Ver granja actual
/help - Ver todos los comandos

¡Estoy listo para ayudarte! ¿Qué transacción quieres registrar hoy? 😊"""

def format_date_for_display(date_str: str) -> str:
    """
    Convert date from YYYY-MM-DD format to DD/MM/YYYY format for display.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Formatted date string in DD/MM/YYYY format
    """
    try:
        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        else:
            # If no date provided, use today's date
            return date.today().strftime("%d/%m/%Y")
    except ValueError:
        # If invalid date format, use today's date as fallback
        return date.today().strftime("%d/%m/%Y")

def format_currency_value(value: str) -> str:
    """Format currency value for display."""
    # Attempt to extract a numeric component first to avoid ValueError when the
    # input contains additional text such as currency symbols or words.
    numeric_part = extract_numeric(str(value)) if value else None

    if numeric_part is None:
        return f"${value}" if value else ""

    try:
        numeric_value = float(numeric_part)
        return f"${numeric_value:,.0f}"
    except ValueError:
        return f"${value}" if value else ""

async def fetch_selected_farm_if_exists(chat_id: int) -> Optional[FarmDTO]:
    async with AsyncSessionLocal() as db:
        selected_farm = await farm_service.get_selected_farm(chat_id=chat_id, session=db)
        if not selected_farm:
            return None
        return selected_farm

async def handle_regular_message(message: Message):
    if not message.from_user:
        await message.answer("❌ No se pudo identificar al usuario. Por favor, intenta nuevamente.")
        return
    user_id = message.from_user.id
    user_input = message.text.strip() if message.text else ""

    chat_id = message.chat.id
    if not chat_id:
        await message.answer("❌ No se pudo identificar el chat. Por favor, intenta nuevamente.")
        return


    # STEP 1: Check if there is a selected farm
    selected_farm = await fetch_selected_farm_if_exists(chat_id=chat_id)
    if not selected_farm:
        await message.answer(
            "❌ Necesitas seleccionar una granja primero.\n\nPor favor use /selectfarm para elegir una granja con la que trabajar."
        )
        return

    # STEP 2: Verificar si el usuario está completando campos faltantes
    if user_id in user_states and user_states[user_id].get("missing_fields"):
        await handle_missing_field_completion(message, user_id, user_input, selected_farm)
        return

    # STEP 3: Si no hay estado previo, procesar el mensaje normalmente
    if not user_input:
        await message.answer("⚠️ El mensaje está vacío. Por favor, escribe algo para que pueda ayudarte.")
        return

    # STEP 4: Procesar mensaje con IA y validar campos
    try:
        await process_new_message(message, user_input, selected_farm, user_id)
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await message.answer(
            "❌ Lo siento, hubo un error procesando tu mensaje. Por favor, intenta nuevamente."
        )


async def show_field_progress(message: Message, user_id: int, state: dict, completed_field: str = ""):
    """Show progress of field completion to the user."""
    api_response = state["api_response"]
    clasificacion = state.get("clasificacion", "")
    
    # Create a summary of completed fields
    completed_fields = []
    for field, value in api_response.items():
        if value and field not in ["farm_id", "date"]:  # Skip system fields
            field_display_names = {
                "note": "📝 Descripción",
                "value": "💰 Valor",
                "type": "📂 Tipo",
                "crop_variety": "🌱 Cultivo",
                "customer": "👤 Cliente",
                "quantity": "📊 Cantidad",
                "quantity_unit": "📏 Unidad"
            }
            display_name = field_display_names.get(field, field)
            completed_fields.append(f"✅ {display_name}: {value}")
    
    if completed_fields:
        progress_message = f"📋 **Progreso de la transacción:**\n\n"
        progress_message += "\n".join(completed_fields)
        
        if completed_field:
            progress_message += f"\n\n🎉 **Campo completado:** {completed_field}"
        
        await message.answer(progress_message)


async def handle_missing_field_completion(message: Message, user_id: int, user_input: str, selected_farm):
    """Handle completion of missing fields by the user."""
    state = user_states[user_id]

    missing_field = state["missing_fields"].pop(0)  # Obtener el siguiente campo faltante

    # --- Normalise value field ------------------------------------------- #
    if missing_field == "value":
        numeric_part = extract_numeric(user_input)
        if numeric_part is None:
            # Reinstate field so the user can try again and prompt for value
            state["missing_fields"].insert(0, missing_field)
            await message.answer("❌ No se pudo identificar un número en tu respuesta. Por favor, ingresa solo el monto, por ejemplo: 1000")
            return
        state["api_response"][missing_field] = numeric_part
    else:
        state["api_response"][missing_field] = user_input  # Guardar el valor proporcionado

    logging.info(f"User {user_id} provided value for missing field '{missing_field}': {user_input}")


    # if not is_valid:
    #     # If invalid, re-add the field to the front of the list and ask again
    #     state["missing_fields"].insert(0, missing_field)
        
    #     # Provide more helpful error messages with examples
    #     enhanced_error = await enhance_error_message(error_message, missing_field, state)
    #     await message.answer(enhanced_error)
    #     await request_next_missing_field(message, user_id, missing_field)
    #     return

    # If valid, save the value
    state["api_response"][missing_field] = user_input
    logging.info(f"User {user_id} provided valid value for missing field '{missing_field}': {user_input}")

    # If there are still missing fields, request the next one
    if state["missing_fields"]:
        remaining_count = len(state["missing_fields"])
        await message.answer(f"🔄 **Faltan {remaining_count} campo(s) por completar.**")
        await request_next_missing_field(message, user_id, state["missing_fields"][0])
        return
    else:
        # All fields are complete, process the transaction
        api_response = state["api_response"]
        clasificacion = state.get("clasificacion", "")
        respuesta = state["respuesta"]

        
        # Id de la sesión de chat de Telegram
        chat_session_id = message.chat.id
        

        # ADD FARM ID TO API RESPONSE
        api_response["farm_id"] = selected_farm.litefarm_farm_id

        # Apply default customer if empty for revenue
        if clasificacion == "ingreso" and not api_response.get("customer"):
            api_response["customer"] = "Cliente General"

        # Final validation of all completed fields
        if clasificacion == "gasto":
            missing_fields, validation_error = validate_expense_fields(api_response)
        elif clasificacion == "ingreso":
            missing_fields, validation_error = validate_revenue_fields(api_response)
        else:
            missing_fields, validation_error = [], ""

        if missing_fields:
            # This should ideally not happen if per-field validation is robust, but as a fallback
            await message.answer(f"Hubo un problema con los datos finales. {validation_error}")
            # We don't delete the state here, so the user can try to fix it, maybe by restarting the command.
            # Or we could re-initiate the missing fields flow. For now, we stop.
            del user_states[user_id] # Or handle this case more gracefully
            return


        # -----------------------------------------------------------------
        # Validación adicional: comprobar que la variedad de cultivo exista
        # -----------------------------------------------------------------
        # Cargamos nuevamente los tipos de ingreso y las variedades para
        # validar que lo que el usuario ingresó sea coherente con la
        # configuración de la granja.
        # validar que es ingreso y la clasificacion es de crop
        if clasificacion == "ingreso" and str(api_response.get("type")) == "1":
            revenue_types = await request_revenue_types(chat_session_id)
            if revenue_types is None or len(revenue_types) < 1:
                await message.answer("Hubo un error en el servidor obteniendo tipos de ingresos, intentalo mas tarde.")
                return

            is_valid_revenue, revenue_name, revenue_error = validate_revenue_type(api_response, revenue_types)
            if not is_valid_revenue:
                await message.answer(revenue_error)
                return

            # La heurística para determinar venta de cultivo es la misma usada
            # en otros puntos del código.
            is_crop_sale = str(api_response.get("type")) == "1" or revenue_name.strip().lower() == "crop sale"
            if is_crop_sale:
                crop_varieties = await request_crop_varieties(chat_session_id)
                if crop_varieties is None:
                    await message.answer("Hubo un error en el servidor obteniendo variedades de cultivos, inténtalo más tarde.")
                    return

                is_valid_crop, crop_name, crop_error = validate_crop_variety(api_response, crop_varieties)
                if not is_valid_crop:
                    await message.answer(crop_error)
                    return

        # Validar contexto de la transacción

        from services.api_service import get_valid_token_for_chat, get_selected_farm_id
        
        chat_session_id = message.chat.id
        token = await get_valid_token_for_chat(chat_session_id)
        farm_id = await get_selected_farm_id(chat_session_id)
        
        context_valid, context_error = validate_transaction_context(
            chat_session_id, farm_id, str(token) if token is not None else ""
        )
        if not context_valid:
            await message.answer(context_error)
            del user_states[user_id] # Clean up state on context error
            return
        
        # Check if validation is enabled for this user
        validation_enabled = get_validation_enabled(user_id)

        # Clear user state *before* final processing
        del user_states[user_id]
        
        if validation_enabled:
            # Show confirmation message if validation is enabled
            await show_confirmation_message(message, respuesta, api_response, clasificacion, user_id)
        else:
            # Process transaction directly if validation is disabled
            await process_transaction_directly(message, respuesta, api_response, clasificacion)


async def enhance_error_message(error_message: str, field_name: str, state: dict) -> str:
    """Enhance error messages with field-specific examples and guidance."""
    enhanced_message = error_message
    
    # Add field-specific examples and guidance
    field_examples = {
        "value": "\n\n💡 **Ejemplos válidos:**\n• 1000\n• 1,500\n• $2500\n• 75.50",
        "note": "\n\n💡 **Ejemplos válidos:**\n• Compra de fertilizante\n• Venta de tomates\n• Pago de mano de obra\n• Mantenimiento de equipos",
        "type": "\n\n💡 **Tipos disponibles:**\n• Para gastos: Fertilizante, Pesticidas, Mano de obra, etc.\n• Para ingresos: Venta de cultivos, Servicios, Otros",
        "customer": "\n\n💡 **Ejemplos válidos:**\n• Juan Pérez\n• Cooperativa del Campo\n• Restaurante El Buen Sabor\n• Mercado Central",
        "quantity": "\n\n💡 **Ejemplos válidos:**\n• 10\n• 25.5\n• 100",
        "quantity_unit": "\n\n💡 **Unidades válidas:**\n• kg, g, lb, ton\n• unidades, piezas\n• litros, ml, galones\n• cajas, sacos"
    }
    
    # Special handling for crop_variety - don't add examples since validation already shows available crops
    if field_name == "crop_variety":
        enhanced_message += "\n\n🔄 **Puedes intentar de nuevo o usar /cancel para cancelar la transacción.**"
        return enhanced_message
    
    if field_name in field_examples:
        enhanced_message += field_examples[field_name]
    
    # Add general guidance
    enhanced_message += "\n\n🔄 **Puedes intentar de nuevo o usar /cancel para cancelar la transacción.**"
    
    return enhanced_message

async def request_next_missing_field(message: Message, user_id: int, field_name: str):
    """Request the next missing field from the user."""
    # Create inline keyboard with cancel button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_incomplete_{user_id}")]
    ])
    
    # Special handling for crop variety field - show available crops
    if field_name == "crop_variety":
        await request_crop_variety_selection(message, user_id)
        return
    
    # Enhanced field messages with examples and guidance
    field_messages = {
        "value": (
            "💰 **Por favor, ingresa el valor/monto de la transacción:**\n\n"
            "💡 **Ejemplos:**\n"
            "• 1000 (mil dólares)\n"
            "• 1,500 (mil quinientos)\n"
            "• $2500 (dos mil quinientos)\n"
            "• 75.50 (setenta y cinco con cincuenta centavos)"
        ),
        "note": (
            "📝 **Por favor, proporciona una descripción de la transacción:**\n\n"
            "💡 **Ejemplos:**\n"
            "• Compra de fertilizante para el maíz\n"
            "• Venta de tomates al mercado\n"
            "• Pago de mano de obra para cosecha\n"
            "• Mantenimiento del tractor"
        ),
        "type": (
            "📂 **Por favor, indica el tipo de transacción:**\n\n"
            "💡 **Tipos disponibles:**\n"
            "• Para gastos: Fertilizante, Pesticidas, Mano de obra, etc.\n"
            "• Para ingresos: Venta de cultivos, Servicios, Otros\n\n"
            "📋 Puedes escribir el nombre o ID del tipo"
        ),
        "customer": (
            "👤 **Por favor, indica el nombre del cliente:**\n\n"
            "💡 **Ejemplos:**\n"
            "• Juan Pérez\n"
            "• Cooperativa del Campo\n"
            "• Restaurante El Buen Sabor\n"
            "• Mercado Central\n\n"
            "💡 O escribe /skip para usar 'Cliente General'"
        ),
        "quantity": (
            "📊 **Por favor, indica la cantidad vendida:**\n\n"
            "💡 **Ejemplos:**\n"
            "• 10 (diez unidades)\n"
            "• 25.5 (veinticinco y medio)\n"
            "• 100 (cien unidades)\n\n"
            "📋 Solo el número, sin la unidad"
        ),
        "quantity_unit": (
            "📏 **Por favor, indica la unidad de medida:**\n\n"
            "💡 **Unidades válidas:**\n"
            "• kg, g, lb, ton (peso)\n"
            "• unidades, piezas (cantidad)\n"
            "• litros, ml, galones (volumen)\n"
            "• cajas, sacos (empaque)\n\n"
            "📋 Escribe solo la unidad (ej: kg, unidades, litros)"
        )
    }
    
    message_text = field_messages.get(field_name, f"Por favor, proporciona el campo: {field_name}")
    await message.answer(message_text, reply_markup=keyboard)


async def request_crop_variety_selection(message: Message, user_id: int):
    """Show available crops for selection with inline buttons."""
    from services.api_service import request_crop_varieties
    
    try:
        # Get available crop varieties for the current farm
        crop_varieties = await request_crop_varieties(message.chat.id)
        
        if not crop_varieties or len(crop_varieties) == 0:
            await message.answer(
                "🌱 **No hay cultivos registrados en tu granja.**\n\n"
                "📝 **Para registrar ventas de cultivos, necesitas:**\n"
                "1. Ir a tu página de LiteFarm\n"
                "2. Registrar al menos un cultivo en tu granja\n"
                "3. Volver aquí para registrar la venta\n\n"
                "💡 Una vez que tengas cultivos registrados, podrás seleccionarlos fácilmente.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_incomplete_{user_id}")]
                ])
            )
            return
        
        # Create buttons for each crop variety
        buttons = []
        for crop in crop_varieties:
            crop_id = crop.get("crop_variety_id", "")
            crop_name = crop.get("crop_variety_name", "")
            if crop_id and crop_name:
                # Create compact callback data to avoid BUTTON_DATA_INVALID error
                # Format: crop_{user_id}_{crop_id} (crop name will be retrieved from API later)
                callback_data = f"crop_{user_id}_{crop_id}"
                
                # Validate callback data length (Telegram limit is 64 bytes)
                if len(callback_data) > 60:  # Leave some buffer
                    print(f"Warning: Callback data too long for crop {crop_name}: {len(callback_data)} bytes")
                    continue
                
                # Truncate crop name if too long for button text
                display_name = crop_name[:20] + "..." if len(crop_name) > 20 else crop_name
                
                buttons.append([
                    InlineKeyboardButton(
                        text=f"🌱 {display_name}",
                        callback_data=callback_data
                    )
                ])
        
        if not buttons:
            await message.answer(
                "🌱 **Error al cargar los cultivos.**\n\n"
                "No se pudieron cargar los cultivos de tu granja. Por favor, intenta nuevamente.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_incomplete_{user_id}")]
                ])
            )
            return
        
        # Add cancel button
        buttons.append([InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_incomplete_{user_id}")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.answer(
            "🌱 **Selecciona el cultivo que vendiste:**\n\n"
            "Elige uno de los cultivos disponibles en tu granja:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        print(f"Error in request_crop_variety_selection: {e}")
        await message.answer(
            "❌ **Error al cargar los cultivos.**\n\n"
            "Hubo un problema al obtener los cultivos de tu granja. Por favor, intenta nuevamente.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_incomplete_{user_id}")]
            ])
        )


async def process_new_message(message: Message, user_input: str, selected_farm, user_id: int):
    """Process a new message with AI and validate fields."""
    # Mostrar escritura mientras se obtienen datos y se procesa la IA
    async with show_typing(message):
        chat_session_id = message.chat.id
        
        # Solicitar todos los tipos de datos
        expense_type = await request_expense_types(chat_session_id)
        if expense_type is None:
            await message.answer("Hubo un error en el servidor obteniendo tipos de gastos, intentalo mas tarde.")
            return
        
        revenue_type = await request_revenue_types(chat_session_id)
        if revenue_type is None or len(revenue_type) < 1:
            await message.answer("Hubo un error en el servidor obteniendo tipos de ingresos, intentalo mas tarde.")
            return

        # Get crop varieties but don't fail immediately if empty
        crop_varieties = await request_crop_varieties(chat_session_id)

        # Crop varieties are only required when the user is recording a revenue transaction.
        # It's possible for a farm to not have any varieties configured yet, so an empty list
        # shouldn't be treated as a hard error that blocks every interaction.
        if crop_varieties is None:
            await message.answer("Hubo un error en el servidor obteniendo variedades de cultivos, inténtalo más tarde.")
            return


        # Consultar el modelo de IA
        response_text = await query_ai_model(user_input, expense_type, revenue_type, crop_varieties or [])

    # Procesar la respuesta de la IA
    try:
        data = json.loads(response_text)
        clasificacion = data.get("clasificacion")
        respuesta = data.get("respuesta")
        api_response = data.get("respuesta_api", {
            "note": "", "value": "", "type": "", "date": "", "crop_variety": "", "customer": ""
        })

        # ADD FARM ID TO API RESPONSE
        api_response["farm_id"] = selected_farm.litefarm_farm_id

        # Handle different classifications
        if clasificacion == "no_relacionado":
            respuesta += "\n\nℹ️ Si necesitas ayuda, escribe /help para ver los comandos disponibles y ejemplos de uso."
            await message.answer(respuesta)
            return
        
        if clasificacion == "saludo":
            await message.answer(respuesta)
            return

        # If cant clasify a crop variety and clasification is "ingreso", is imposible to register the income
        if clasificacion == "ingreso" and not api_response.get("crop_variety"):
            await message.answer("❌ No puedo registrar el ingreso porque no tienes la variedad de cultivo en tu granja.")
            return

        print(f"Clasificación: {clasificacion}, Respuesta: {respuesta}, API Response: {api_response}")
        # Validate API response types and generate user-friendly messages
        if clasificacion == "gasto":
            await process_expense_classification(message, api_response, expense_type, selected_farm, respuesta)
        elif clasificacion == "ingreso":
            await process_revenue_classification(message, api_response, revenue_type, crop_varieties or [], selected_farm, respuesta)
        
        # STEP 4: Verificar campos requeridos y manejar campos faltantes
        missing_fields = []
        validation_error = ""
        
        if clasificacion == "gasto":
            missing_fields, validation_error = validate_expense_fields(api_response)
            # También validar que el tipo de gasto existe
            if not missing_fields and expense_type:
                is_valid_expense, expense_name, expense_error = validate_expense_type(api_response, expense_type)
                if not is_valid_expense:
                    await message.answer(expense_error)
                    return
        elif clasificacion == "ingreso":
            missing_fields, validation_error = validate_revenue_fields(api_response)
            
            # Check if this is a crop sale and crop varieties are needed but not available
            if "crop_variety" in missing_fields and (crop_varieties is None or len(crop_varieties) < 1):
                await message.answer(
                    "🌱 **Para registrar ventas de cultivos, necesitas tener cultivos registrados en tu granja.**\n\n"
                    "📝 **Por favor:**\n"
                    "1. Ve a tu página de LiteFarm\n"
                    "2. Registra al menos un cultivo en tu granja\n"
                    "3. Vuelve aquí para registrar la venta\n\n"
                    "💡 Una vez que tengas cultivos registrados, podrás registrar ventas sin problemas."
                )
                return

        # Si faltan campos, solicitar el primero y guardar estado
        if missing_fields:
            user_states[user_id] = {
                "missing_fields": missing_fields,
                "api_response": api_response,
                "respuesta": respuesta,
                "clasificacion": clasificacion,
            }
            await request_next_missing_field(message, user_id, missing_fields[0])
            return

        # Si todos los campos están completos, validar contexto y procesar
        await finalize_transaction(message, api_response, clasificacion, respuesta, user_id)

    except json.JSONDecodeError:
        logging.warning("Respuesta del modelo no tiene formato JSON válido. Respuesta recibida: %s", response_text)
        await message.answer(
            "❌ Lo siento, no entendí tu mensaje o hubo un error procesando la respuesta. "
            "Por favor, intenta reformular tu mensaje o usa /help para ver ejemplos de uso."
        )


async def process_expense_classification(message: Message, api_response: dict, expense_type: list, selected_farm, respuesta: str):
    """Process expense classification and update response message."""
    if expense_type and api_response.get("type"):
        selected_type = api_response.get("type")
        selected_name = ""

        # Find the name of the selected expense type
        for item in expense_type:
            if isinstance(item, dict) and str(item.get('expense_type_id', '')) == str(selected_type):
                selected_name = item.get('expense_name', '')
                break

        if not selected_name and selected_type:
            selected_name = selected_type

        # Update response with transaction details
        note = api_response.get("note", "")
        value = api_response.get("value", "")
        transaction_date = format_date_for_display(api_response.get("date", ""))
        formatted_value = format_currency_value(value)

        api_response["formatted_response"] = f"Seleccioné este tipo: {selected_name}\n\n¡Listo! He registrado {note.lower()} por {formatted_value} el dia {transaction_date} como gasto de {selected_name.lower()} en la granja **{selected_farm.name}** 🚜💸. Si tienes más gastos o ingresos para registrar, avísame."


async def process_revenue_classification(message: Message, api_response: dict, revenue_type: list, crop_varieties: list, selected_farm, respuesta: str):
    print(f"Processing revenue classification with API response: {api_response}, revenue_type: {revenue_type}, crop_varieties: {crop_varieties}, selected_farm: {selected_farm}, respuesta: {respuesta}")
    """Process revenue classification and update response message."""
    # Validate revenue type
    is_valid_revenue, revenue_name, revenue_error = validate_revenue_type(api_response, revenue_type)
    if not is_valid_revenue:
        await message.answer(revenue_error)
        return


    # Check if it's a crop sale and validate crop variety.
    # According to LiteFarm, revenue_type_id == 1 represents crop sales, but we
    # also keep the legacy "crop sale" name check for safety.
    selected_crop_name = revenue_name
    is_crop_sale = str(api_response.get("type")) == "1" or revenue_name.strip().lower() == "crop sale"

    if is_crop_sale:
        is_valid_crop, crop_name, crop_error = validate_crop_variety(api_response, crop_varieties)
        if not is_valid_crop:
            # Early-exit if the crop variety provided by the user is not present
            # in the farm.  This prevents the bot from entering a loop asking
            # for missing fields that will never validate.
            await message.answer(crop_error)
            return
        selected_crop_name = crop_name

    # Handle customer field - set default if empty
    customer_name = api_response.get("customer", "").strip()
    if not customer_name:
        api_response["customer"] = "Cliente General"
        customer_name = "Cliente General"

    # Build the human-friendly confirmation/response text regardless of the
    # revenue type so that later stages can simply reuse it.
    note = api_response.get("note", "")
    value = api_response.get("value", "")
    transaction_date = format_date_for_display(api_response.get("date", ""))
    formatted_value = format_currency_value(value)


    api_response["formatted_response"] = (
        f"Seleccioné este tipo: {revenue_name}\n\n¡Listo! He registrado {note.lower()} por {formatted_value} el dia {transaction_date} "
        f"como ingreso de {selected_crop_name.lower()} para el cliente {customer_name} en la granja **{selected_farm.name}** 🚜💰. "
        "Si tienes más ingresos o gastos para registrar, avísame."
    )



async def finalize_transaction(message: Message, api_response: dict, clasificacion: str, respuesta: str, user_id: int):
    """Finalize transaction after all validations pass."""
    # Validar contexto de la transacción
    from services.api_service import get_valid_token_for_chat, get_selected_farm_id
    
    chat_session_id = message.chat.id
    token = await get_valid_token_for_chat(chat_session_id)
    farm_id = await get_selected_farm_id(chat_session_id)
    
    context_valid, context_error = validate_transaction_context(
        chat_session_id, farm_id, str(token) if token is not None else ""
    )
    if not context_valid:
        await message.answer(context_error)
        return

    # ---------------------------------------------------------------------
    # Extra validation for revenue transactions completed a posteriori
    # ---------------------------------------------------------------------
    if clasificacion == "ingreso":
        # Fetch latest reference data so we can validate again now that the
        # user might have supplied any missing fields (e.g. crop variety).
        revenue_types = await request_revenue_types(chat_session_id)
        if revenue_types is None or len(revenue_types) < 1:
            await message.answer("Hubo un error en el servidor obteniendo tipos de ingresos, intentalo mas tarde.")
            return

        # Validate that the revenue type still exists
        is_valid_revenue, revenue_name, revenue_error = validate_revenue_type(api_response, revenue_types)
        if not is_valid_revenue:
            await message.answer(revenue_error)
            return

        # If it is a crop sale (revenue_type_id == 1) validate the crop
        # variety against the farm catalogue. We reuse the same heuristic used
        # earlier (type == 1 or revenue name == "crop sale").
        is_crop_sale = str(api_response.get("type")) == "1" or revenue_name.strip().lower() == "crop sale"
        if is_crop_sale:
            crop_varieties = await request_crop_varieties(chat_session_id)
            if crop_varieties is None:
                await message.answer("Hubo un error en el servidor obteniendo variedades de cultivos, inténtalo más tarde.")
                return

            is_valid_crop, crop_name, crop_error = validate_crop_variety(api_response, crop_varieties)
            if not is_valid_crop:
                await message.answer(crop_error)
                return

    # Apply default customer if empty for revenue
    if clasificacion == "ingreso" and not api_response.get("customer"):
        api_response["customer"] = "Cliente General"

    # Use formatted response if available
    final_respuesta = api_response.get("formatted_response", respuesta)
    
    # Check if validation is enabled for this user
    validation_enabled = get_validation_enabled(user_id)
    
    if validation_enabled:
        # Show confirmation message if validation is enabled
        await show_confirmation_message(message, final_respuesta, api_response, clasificacion, user_id)
    else:
        # Process transaction directly if validation is disabled
        await process_transaction_directly(message, final_respuesta, api_response, clasificacion)

async def process_transaction_directly(message: Message, transaction_details: str, api_response: dict, clasificacion: str):
    """
    Process transaction directly without confirmation when validation is disabled.
    """
    try:
        # Show typing while processing transaction
        async with show_typing(message):
            await handle_api_transaction(api_response, clasificacion, message=message)
        
        #TODO: Add logic to handle the response from the API if needed
        # Create success message
        await message.answer(f"✅ Transacción registrada exitosamente:\n\n{transaction_details}")
        
    except Exception as e:
        logging.error(f"Error processing transaction directly: {e}")
        await message.answer(
            "❌ Error al procesar la transacción. Por favor, intenta nuevamente."
        )

async def show_confirmation_message(message: Message, transaction_details: str, api_response: dict, clasificacion: str, user_id: int):
    """
    Show confirmation message with options to confirm or cancel.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data=f"confirm_transaction_{user_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_transaction_{user_id}")
        ]
    ])
    
    # Store api_response in user_states for later use
    if user_id not in user_states:
        user_states[user_id] = {}
        
    user_states[user_id]["confirmation_data"] = {
        "api_response": api_response,
        "clasificacion": clasificacion
    }
    
    await message.answer(
        f"⏳ Por favor, confirma los detalles de la transacción:\n\n{transaction_details}",
        reply_markup=keyboard
    )