import json
import logging
from datetime import datetime, date
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ChatAction
from services.ai_service import query_ai_model
from services.api_service import handle_api_transaction, request_expense_types, request_revenue_types, request_crop_varieties
from services.typing_context import show_typing
from commands.disable_validation import get_validation_enabled
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

def validate_revenue_type(api_response: dict, revenue_types: list) -> tuple[bool, str, str]:
    """
    Validate if the revenue type exists in the available revenue types.
    
    Returns:
        tuple: (is_valid, revenue_type_name, error_message)
    """
    selected_revenue_type = api_response.get("type", "")
    
    # Convert to string and strip if it's not already a string
    if isinstance(selected_revenue_type, (int, float)):
        selected_revenue_type = str(selected_revenue_type)
    else:
        selected_revenue_type = str(selected_revenue_type).strip()
    
    available_revenue_types = [f"ID: {item.get('revenue_type_id')} - {item.get('revenue_name')}" for item in revenue_types if isinstance(item, dict)]
    
    # Find the revenue type by ID
    for item in revenue_types:
        if isinstance(item, dict) and str(item.get('revenue_type_id', '')) == str(selected_revenue_type):
            return True, item.get('revenue_name', ''), ""
    
    # If not found, create error message with available options
    revenue_options = [
        f"• {item.get('revenue_name', '')}" 
        for item in revenue_types 
        if isinstance(item, dict) and item.get('revenue_name')
    ]
    
    error_msg = (
        "No pude identificar un tipo de ingreso específico. "
        "Por favor, asegúrate de que el mensaje incluya un tipo de ingreso válido.\n\n"
        f"Tipos de ingresos disponibles:\n{chr(10).join(revenue_options)}"
    )
    
    return False, "", error_msg

def validate_crop_variety(api_response: dict, crop_varieties: list) -> tuple[bool, str, str]:
    """
    Validate if the crop variety exists in the available crop varieties.
    
    Returns:
        tuple: (is_valid, crop_variety_name, error_message)
    """
    crop_variety_id = api_response.get("crop_variety", "")
    
    # Enhanced logging for debugging
    available_varieties = [f"ID: {item.get('crop_variety_id')} - {item.get('crop_variety_name')}" for item in crop_varieties if isinstance(item, dict)]
    
    if not crop_variety_id:
        # Create available crop varieties list for error message
        crop_variety_list = "\n".join(
            f"• {item.get('crop_variety_name', '')}"
            for item in crop_varieties 
            if isinstance(item, dict) and item.get('crop_variety_name')
        )
        
        error_msg = (
            "No pude identificar una variedad de cultivo disponible en tu granja. "
            "Por favor, asegúrate de que el mensaje incluya una variedad de cultivo válida.\n\n"
            f"Variedades de cultivo disponibles:\n{crop_variety_list}"
        )
        
        return False, "", error_msg
    
    # Find the crop variety by ID
    for item in crop_varieties:
        if isinstance(item, dict) and str(item.get('crop_variety_id', '')) == str(crop_variety_id):
            crop_name = item.get('crop_variety_name', '')
            return True, f"Venta de {crop_name}", ""
    
    # If crop variety ID not found in list
    crop_variety_list = "\n".join(
        f"• {item.get('crop_variety_name', '')}"
        for item in crop_varieties 
        if isinstance(item, dict) and item.get('crop_variety_name')
    )
    
    error_msg = (
        "No pude identificar una variedad de cultivo específica para la venta. "
        "Por favor, asegúrate de que el mensaje incluya una variedad de cultivo válida.\n\n"
        f"Variedades de cultivo disponibles:\n{crop_variety_list}"
    )
    
    return False, "", error_msg

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
        loggger.info(f"Checking selected farm for chat_id: {chat_id}")
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

    loggger.info(f"User {user_id} sent message: {user_input}")

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

    # Verificar si el usuario está completando un campo faltante
    if user_id in user_states:
        state = user_states[user_id]
        missing_field = state["missing_fields"].pop(0)  # Obtener el siguiente campo faltante
        state["api_response"][missing_field] = user_input  # Guardar el valor proporcionado

        # Si aún faltan campos, solicitar el siguiente
        if state["missing_fields"]:
            # Create inline keyboard with cancel button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_incomplete_{user_id}")]
            ])
            
            next_field = state["missing_fields"][0]
            if next_field == "value":
                await message.answer("💰 Por favor, ingresa el precio de la transacción:", reply_markup=keyboard)
            elif next_field == "note":
                await message.answer("📝 Por favor, proporciona una breve descripción de la transacción:", reply_markup=keyboard)
            elif next_field == "type":
                await message.answer("📂 Por favor, indica el tipo de transacción (por ejemplo: gasolina, maquinaria, plantas, otro):", reply_markup=keyboard)
            return
        else:
            # Todos los campos están completos
            api_response = state["api_response"]
            clasificacion = state.get("clasificacion", "")
            respuesta = state["respuesta"]
            
            # ADD FARM ID TO API RESPONSE - Add this line
            api_response["farm_id"] = selected_farm.litefarm_farm_id
            
            del user_states[user_id]
            
            # Apply default customer if empty for revenue
            if api_response.get("customer") == "":
                api_response["customer"] = "Cliente General"
            
            # Check if validation is enabled for this user
            user_id = message.from_user.id
            validation_enabled = get_validation_enabled(user_id)
            
            if validation_enabled:
                # Show confirmation message if validation is enabled
                await show_confirmation_message(message, respuesta, api_response, clasificacion)
            else:
                # Process transaction directly if validation is disabled
                await process_transaction_directly(message, respuesta, api_response, clasificacion)
            return

    # Si no hay estado previo, procesar el mensaje normalmente
    if not user_input:
        await message.answer("⚠️ El mensaje está vacío. Por favor, escribe algo para que pueda ayudarte.")
        return

    # Mostrar escritura mientras se obtienen datos y se procesa la IA
    async with show_typing(message):
        # Solicitar todos los tipos de datos
        expense_type = await request_expense_types()
        if expense_type is None:
            await message.answer("Hubo un error en el servidor obteniendo tipos de gastos, intentalo mas tarde.")
            return
        
        revenue_type = await request_revenue_types()
        if revenue_type is None or len(revenue_type) < 1:
            await message.answer("Hubo un error en el servidor obteniendo tipos de ingresos, intentalo mas tarde.")
            return

        crop_varieties = await request_crop_varieties()
        
        if crop_varieties is None or len(crop_varieties) < 1:
            await message.answer("Hubo un error en el servidor obteniendo variedades de cultivos, intentalo mas tarde.")
            return

        # Consultar el modelo de IA
        response_text = await query_ai_model(user_input, expense_type, revenue_type, crop_varieties)

    # Procesar la respuesta (sin necesidad de escribir aquí ya que es rápido)
    try:
        data = json.loads(response_text)

        clasificacion = data.get("clasificacion")
        respuesta = data.get("respuesta")
        api_response = data.get("respuesta_api", {
            "note": "", "value": "", "type": "", "date": "", "crop_variety": "", "customer": ""
        })

        # ADD FARM ID TO API RESPONSE - Add this line right after getting api_response
        api_response["farm_id"] = selected_farm.litefarm_farm_id

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

                # Get the transaction details for display
                note = api_response.get("note", "")
                value = api_response.get("value", "")
                transaction_date = format_date_for_display(api_response.get("date", ""))
                formatted_value = format_currency_value(value)

                # INCLUDE FARM NAME IN RESPONSE MESSAGE - Update response to include farm info
                respuesta = f"Seleccioné este tipo: {selected_name}\n\n¡Listo! He registrado {note.lower()} por {formatted_value} el dia {transaction_date} como gasto de {selected_name.lower()} en la granja **{selected_farm.name}** 🚜💸. Si tienes más gastos o ingresos para registrar, avísame."
            else:
                respuesta = "No pude identificar un tipo de gasto específico. Por favor, asegúrate de que el mensaje incluya un tipo de gasto válido.\n\n" + respuesta

        # Handle revenue classification
        elif clasificacion == "ingreso":
            # Validate revenue type
            is_valid_revenue, revenue_name, revenue_error = validate_revenue_type(api_response, revenue_type)
            
            if not is_valid_revenue:
                await message.answer(revenue_error)
                return
            
            # Check if it's a crop sale and validate crop variety
            selected_crop_name = revenue_name  # Default to revenue type name
            
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

            # Format transaction details
            note = api_response.get("note", "")
            value = api_response.get("value", "")
            transaction_date = format_date_for_display(api_response.get("date", ""))
            formatted_value = format_currency_value(value)
            
            # INCLUDE FARM NAME IN RESPONSE MESSAGE - Update response to include farm info
            respuesta = f"Seleccioné este tipo: {revenue_name}\n\n¡Listo! He registrado {note.lower()} por {formatted_value} el dia {transaction_date} como ingreso de {selected_crop_name.lower()} para el cliente {customer_name} en la granja **{selected_farm.name}** 🚜💰. Si tienes más ingresos o gastos para registrar, avísame."

        # Handle non-related classification
        elif clasificacion == "no_relacionado":
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
        # Note: date is optional, if not provided we'll use today's date

        if missing_fields:
            # Guardar el estado del usuario
            user_states[user_id] = {
                "missing_fields": missing_fields,
                "api_response": api_response,  # This already includes farm_id
                "respuesta": respuesta,
                "clasificacion": clasificacion,
            }
            
            # Create inline keyboard with cancel button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_incomplete_{user_id}")]
            ])
            
            first_missing_field = missing_fields[0]
            if first_missing_field == "value":
                await message.answer(
                    "💰 Faltó el precio de la transacción. Por favor, ingrésalo:",
                    reply_markup=keyboard
                )
            elif first_missing_field == "note":
                await message.answer(
                    "📝 Faltó la descripción de la transacción. Por favor, proporciónala:",
                    reply_markup=keyboard
                )
            elif first_missing_field == "type":
                await message.answer(
                    "📂 Faltó el tipo de transacción. Por favor, indícalo (por ejemplo: gasolina, maquinaria, plantas, otro):",
                    reply_markup=keyboard
                )
            return

        # Apply default customer if empty for revenue
        if clasificacion == "ingreso" and not api_response.get("customer"):
            api_response["customer"] = "Cliente General"

        # Process final transaction
        async with show_typing(message):
            await handle_api_transaction(api_response, clasificacion, message)

        # Check if validation is enabled for this user
        user_id = message.from_user.id
        validation_enabled = get_validation_enabled(user_id)
        
        if validation_enabled:
            # Show confirmation message if validation is enabled
            await show_confirmation_message(message, respuesta, api_response, clasificacion)
        else:
            # Process transaction directly if validation is disabled
            await process_transaction_directly(message, respuesta, api_response, clasificacion)

    except json.JSONDecodeError:
        logging.warning("Respuesta del modelo no tiene formato JSON válido. Respuesta recibida: %s", response_text)
        await message.answer(
            "❌ Lo siento, no entendí tu mensaje o hubo un error procesando la respuesta. "
            "Por favor, intenta reformular tu mensaje o usa /help para ver ejemplos de uso."
        )

async def process_transaction_directly(message: Message, transaction_details: str, api_response: dict, clasificacion: str):
    """
    Process transaction directly without confirmation when validation is disabled.
    """
    try:
        # Show typing while processing transaction
        async with show_typing(message):
            await handle_api_transaction(api_response, clasificacion)
        
        # Create success message
        success_message = transaction_details.replace("Voy a registrar", "¡Listo! He registrado")
        success_message += "\n\n✅ Transacción registrada exitosamente. Si tienes más gastos o ingresos para registrar, avísame."
        success_message += "\n\n💡 *Validación deshabilitada* - Para habilitar confirmación usa /habilitar_validacion"
        
        await message.answer(success_message)
        
    except Exception as e:
        logging.error(f"Error processing transaction directly: {e}")
        await message.answer(
            "❌ Error al procesar la transacción. Por favor, intenta nuevamente."
        )

async def show_confirmation_message(message: Message, transaction_details: str, api_response: dict, clasificacion: str):
    """
    Show confirmation message with inline keyboard buttons.
    """
    user_id = message.from_user.id
    
    # Store transaction data for confirmation
    user_states[user_id] = {
        "awaiting_confirmation": True,
        "api_response": api_response,
        "clasificacion": clasificacion,
        "transaction_details": transaction_details
    }
    
    # Create inline keyboard with confirmation buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data=f"confirm_{user_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_{user_id}")
        ]
    ])
    
    confirmation_text = f"{transaction_details}\n\n¿Estás seguro de realizar la acción?"
    
    await message.answer(confirmation_text, reply_markup=keyboard)