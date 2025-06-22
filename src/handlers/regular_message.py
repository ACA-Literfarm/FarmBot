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
logging.basicConfig(level=logging.INFO)
loggger = logging.getLogger(__name__)

farm_service = FarmSelectionService(
    repo_factory=FarmRepository,  # Replace with actual repository factory if needed
    chat_session_repo_factory=ChatSessionRepository  # Replace with actual chat session repository
)

# Diccionario para rastrear el estado del usuario
user_states = {}

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
    try:
        if value:
            numeric_value = float(value.replace(",", ""))
            return f"${numeric_value:,.0f}"
        return ""
    except (ValueError, AttributeError):
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

    # Check if there is a selected farm
    selected_farm = await fetch_selected_farm_if_exists(chat_id=chat_id)
    if not selected_farm:
        await message.answer(
            "❌ Necesitas seleccionar una granja primero.\n\nPor favor use /selectfarm para elegir una granja con la que trabajar."
        )
        return

    # STEP 1: Verificar si el usuario está completando campos faltantes
    if user_id in user_states and user_states[user_id].get("missing_fields"):
        await handle_missing_field_completion(message, user_id, user_input, selected_farm)
        return

    # STEP 2: Si no hay estado previo, procesar el mensaje normalmente
    if not user_input:
        await message.answer("⚠️ El mensaje está vacío. Por favor, escribe algo para que pueda ayudarte.")
        return

    # STEP 3: Procesar mensaje con IA y validar campos
    try:
        await process_new_message(message, user_input, selected_farm, user_id)
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await message.answer(
            "❌ Lo siento, hubo un error procesando tu mensaje. Por favor, intenta nuevamente."
        )


async def handle_missing_field_completion(message: Message, user_id: int, user_input: str, selected_farm):
    """Handle completion of missing fields by the user."""
    state = user_states[user_id]
    missing_field = state["missing_fields"].pop(0)  # Get the next missing field

    # Validate the user's input for the specific field
    is_valid, error_message = validate_field(missing_field, user_input)

    if not is_valid:
        # If invalid, re-add the field to the front of the list and ask again
        state["missing_fields"].insert(0, missing_field)
        await message.answer(error_message)
        await request_next_missing_field(message, user_id, missing_field)
        return

    # If valid, save the value
    state["api_response"][missing_field] = user_input
    logging.info(f"User {user_id} provided valid value for missing field '{missing_field}': {user_input}")

    # If there are still missing fields, request the next one
    if state["missing_fields"]:
        await request_next_missing_field(message, user_id, state["missing_fields"][0])
        return
    else:
        # All fields are complete, process the transaction
        api_response = state["api_response"]
        clasificacion = state.get("clasificacion", "")
        respuesta = state["respuesta"]

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

        # Validate transaction context
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


async def request_next_missing_field(message: Message, user_id: int, field_name: str):
    """Request the next missing field from the user."""
    # Create inline keyboard with cancel button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_incomplete_{user_id}")]
    ])
    
    field_messages = {
        "value": "💰 Por favor, ingresa el valor/monto de la transacción:",
        "note": "📝 Por favor, proporciona una descripción de la transacción:",
        "type": "📂 Por favor, indica el tipo de transacción:",
        "crop_variety": "🌱 Por favor, especifica la variedad de cultivo:",
        "customer": "👤 Por favor, indica el nombre del cliente:",
        "quantity": "📊 Por favor, indica la cantidad vendida (ej: 10):",
        "quantity_unit": "📏 Por favor, indica la unidad de medida (ej: kg, unidades, litros):"
    }
    
    message_text = field_messages.get(field_name, f"Por favor, proporciona el campo: {field_name}")
    await message.answer(message_text, reply_markup=keyboard)


async def process_new_message(message: Message, user_input: str, selected_farm, user_id: int):
    """Process a new message with AI and validate fields."""
    # Mostrar escritura mientras se obtienen datos y se procesa la IA
    async with show_typing(message):
        chat_session_id = message.chat.id
        
        # Solicitar todos los tipos de datos
        expense_type = await request_expense_types()
        if expense_type is None:
            await message.answer("Hubo un error en el servidor obteniendo tipos de gastos, intentalo mas tarde.")
            return
        
        revenue_type = await request_revenue_types(chat_session_id)
        if revenue_type is None or len(revenue_type) < 1:
            await message.answer("Hubo un error en el servidor obteniendo tipos de ingresos, intentalo mas tarde.")
            return

        # Get crop varieties but don't fail immediately if empty
        crop_varieties = await request_crop_varieties(chat_session_id)

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

        # Check if this is a sale and crop varieties are needed but not available
        if clasificacion == "ingreso" and (crop_varieties is None or len(crop_varieties) < 1):
            await message.answer(
                "🌱 **Para registrar ventas de cultivos, necesitas tener cultivos registrados en tu granja.**\n\n"
                "📝 **Por favor:**\n"
                "1. Ve a tu página de LiteFarm\n"
                "2. Registra al menos un cultivo en tu granja\n"
                "3. Vuelve aquí para registrar la venta\n\n"
                "💡 Una vez que tengas cultivos registrados, podrás registrar ventas sin problemas."
            )
            return

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
    """Process revenue classification and update response message."""
    # Validate revenue type
    is_valid_revenue, revenue_name, revenue_error = validate_revenue_type(api_response, revenue_type)
    if not is_valid_revenue:
        await message.answer(revenue_error)
        return

    # Check if it's a crop sale and validate crop variety
    selected_crop_name = revenue_name
    if revenue_name.strip().lower() == "crop sale":
        is_valid_crop, crop_name, crop_error = validate_crop_variety(api_response, crop_varieties)
        if not is_valid_crop:
            await message.answer(crop_error)
            return
        selected_crop_name = crop_name

    # Handle customer field - set default if empty
    customer_name = api_response.get("customer", "").strip()
    if not customer_name:
        api_response["customer"] = "Cliente General"
        customer_name = "Cliente General"

    # Update response with transaction details
    note = api_response.get("note", "")
    value = api_response.get("value", "")
    transaction_date = format_date_for_display(api_response.get("date", ""))
    formatted_value = format_currency_value(value)
    
    api_response["formatted_response"] = f"Seleccioné este tipo: {revenue_name}\n\n¡Listo! He registrado {note.lower()} por {formatted_value} el dia {transaction_date} como ingreso de {selected_crop_name.lower()} para el cliente {customer_name} en la granja **{selected_farm.name}** 🚜💰. Si tienes más ingresos o gastos para registrar, avísame."


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