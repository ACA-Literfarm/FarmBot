from aiogram.types import CallbackQuery, Message
from services.api_service import handle_api_transaction, request_crop_varieties, request_revenue_types
from services.typing_context import show_typing
from handlers.regular_message import user_states, request_next_missing_field, show_field_progress, finalize_transaction, process_revenue_classification
from shared.services.farm_selection_service import FarmSelectionService
from shared.repositories.farm_repository import FarmRepository
from shared.repositories.chat_repository import ChatSessionRepository
from shared.db.session import AsyncSessionLocal

farm_service = FarmSelectionService(
    repo_factory=FarmRepository,
    chat_session_repo_factory=ChatSessionRepository
)

async def handle_confirmation_callback(callback: CallbackQuery):
    """
    Handle confirmation and cancellation callbacks.
    """
    try:
        # Check if callback data exists
        if not callback.data:
            await callback.answer("❌ Datos de callback inválidos.", show_alert=True)
            return
            
        # Check if message exists and is accessible
        if not callback.message or not isinstance(callback.message, Message):
            await callback.answer("❌ Mensaje no disponible.", show_alert=True)
            return
        
        # Parse callback data
        callback_parts = callback.data.split("_")
        action = callback_parts[0]
        
        print(f"DEBUG: Callback received - data: {callback.data}, parts: {callback_parts}")
        
        if len(callback_parts) == 3 and callback_parts[1] == "incomplete":
            # Handle incomplete transaction cancellation (format: cancel_incomplete_userID)
            user_id = int(callback_parts[2])
        elif len(callback_parts) == 3 and callback_parts[1] == "transaction":
            # Handle transaction confirmation/cancellation (format: confirm_transaction_userID or cancel_transaction_userID)
            user_id = int(callback_parts[2])
        elif len(callback_parts) == 3 and callback_parts[0] == "crop":
            # Handle crop selection (format: crop_userID_cropID)
            print(f"DEBUG: Detected crop selection callback: {callback.data}")
            await handle_crop_selection_callback(callback)
            return
        else:
            # Handle legacy format (format: confirm_userID or cancel_userID)
            user_id = int(callback_parts[1])
        
        # Verify the callback is from the correct user
        if callback.from_user.id != user_id:
            await callback.answer("❌ Esta acción no es para ti.", show_alert=True)
            return
        
        # Check if user has pending confirmation or incomplete transaction
        if user_id not in user_states:
            await callback.answer("❌ No hay transacción pendiente.", show_alert=True)
            return
        
        state = user_states[user_id]
        
        if action == "confirm":
            # Check for new confirmation data structure
            if "confirmation_data" in state:
                # New structure with confirmation_data
                confirmation_data = state["confirmation_data"]
                api_response = confirmation_data["api_response"]
                clasificacion = confirmation_data["clasificacion"]
                
                # Clear user state
                del user_states[user_id]
                
                # Show typing while processing transaction
                async with show_typing(callback.message):
                    await handle_api_transaction(api_response, clasificacion, callback.message)
                
                # Update message with success response
                try:
                    await callback.message.edit_text("✅ Transacción registrada exitosamente!")
                except Exception:
                    # If message can't be edited, send a new one
                    await callback.message.answer("✅ Transacción registrada exitosamente!")
                await callback.answer("✅ Transacción registrada exitosamente!")
                
            elif state.get("awaiting_confirmation"):
                # Legacy structure
                api_response = state["api_response"]
                clasificacion = state["clasificacion"]
                
                # Clear user state
                del user_states[user_id]
                
                # Show typing while processing transaction
                async with show_typing(callback.message):
                    await handle_api_transaction(api_response, clasificacion, callback.message)
                
                # Update message with success response
                success_message = state["transaction_details"].replace("Voy a registrar", "¡Listo! He registrado")
                success_message += "\n\n✅ Transacción registrada exitosamente. Si tienes más gastos o ingresos para registrar, avísame."
                
                try:
                    await callback.message.edit_text(success_message)
                except Exception:
                    # If message can't be edited, send a new one
                    await callback.message.answer(success_message)
                await callback.answer("✅ Transacción registrada exitosamente!")
            else:
                await callback.answer("❌ No hay transacción pendiente de confirmación.", show_alert=True)
            
        elif action == "cancel":
            # Clear user state
            del user_states[user_id]
            
            if len(callback_parts) == 3 and callback_parts[1] == "incomplete":
                # Handle cancellation of incomplete transactions
                try:
                    await callback.message.edit_text(
                        "❌ Transacción cancelada exitosamente.\n\n"
                        "Puedes enviar otro mensaje para registrar una nueva transacción. "
                        "Si necesitas ayuda, escribe /ayuda para ver ejemplos de uso. 🚜"
                    )
                except Exception:
                    await callback.message.answer(
                        "❌ Transacción cancelada exitosamente.\n\n"
                        "Puedes enviar otro mensaje para registrar una nueva transacción. "
                        "Si necesitas ayuda, escribe /ayuda para ver ejemplos de uso. 🚜"
                    )
                await callback.answer("❌ Transacción cancelada.")
            else:
                # Handle cancellation of complete transactions awaiting confirmation
                try:
                    await callback.message.edit_text("❌ Transacción cancelada. Puedes enviar otro mensaje para registrar una nueva transacción.")
                except Exception:
                    await callback.message.answer("❌ Transacción cancelada. Puedes enviar otro mensaje para registrar una nueva transacción.")
                await callback.answer("❌ Transacción cancelada.")
            
    except Exception as e:
        await callback.answer("❌ Error procesando la confirmación.", show_alert=True)
        print(f"Error in confirmation callback: {e}")


async def handle_crop_selection_callback(callback: CallbackQuery):
    """
    Handle crop selection callbacks.
    Format: crop_userID_cropID
    """
    try:
        # Check if callback data exists
        if not callback.data:
            await callback.answer("❌ Datos de callback inválidos.", show_alert=True)
            return
            
        # Check if message exists and is accessible
        if not callback.message or not isinstance(callback.message, Message):
            await callback.answer("❌ Mensaje no disponible.", show_alert=True)
            return
        
        # Parse callback data
        callback_parts = callback.data.split("_")
        if len(callback_parts) != 3:
            await callback.answer("❌ Formato de callback inválido.", show_alert=True)
            return
        
        user_id = int(callback_parts[1])
        crop_id = callback_parts[2]
        
        # Verify the callback is from the correct user
        if callback.from_user.id != user_id:
            await callback.answer("❌ Esta acción no es para ti.", show_alert=True)
            return
        
        # Check if user has pending state
        if user_id not in user_states:
            await callback.answer("❌ No hay transacción pendiente.", show_alert=True)
            return
        
        state = user_states[user_id]
        
        # Get crop name from API using crop_id
        crop_varieties = await request_crop_varieties(callback.message.chat.id)
        
        crop_name = "Cultivo seleccionado"  # Default fallback
        if crop_varieties:
            for crop in crop_varieties:
                if str(crop.get("crop_variety_id", "")) == str(crop_id):
                    crop_name = crop.get("crop_variety_name", "Cultivo seleccionado")
                    break
        
        # Save the selected crop
        state["api_response"]["crop_variety"] = crop_id
        
        # Remove crop_variety from missing fields
        if "crop_variety" in state["missing_fields"]:
            state["missing_fields"].remove("crop_variety")
        
        # If there are still missing fields, request the next one
        if state["missing_fields"]:
            remaining_count = len(state["missing_fields"])
            await callback.message.answer(f"🔄 **Faltan {remaining_count} campo(s) por completar.**")
            await request_next_missing_field(callback.message, user_id, state["missing_fields"][0])
        else:
            # All fields are complete, process the transaction
            await callback.message.answer("✅ **¡Todos los campos completados!** Procesando la transacción...")
            
            # Get selected farm
            async with AsyncSessionLocal() as db:
                selected_farm = await farm_service.get_selected_farm(chat_id=callback.message.chat.id, session=db)
            
            if not selected_farm:
                await callback.message.answer("❌ Error: No se pudo obtener la granja seleccionada.")
                return
            
            # Process the completed transaction
            api_response = state["api_response"]
            clasificacion = state.get("clasificacion", "")
            respuesta = state["respuesta"]
            
            # Add farm ID to API response
            api_response["farm_id"] = selected_farm.litefarm_farm_id
            
            # Apply default customer if empty for revenue
            if clasificacion == "ingreso" and not api_response.get("customer"):
                api_response["customer"] = "Cliente General"
            
            # Regenerate formatted_response with correct crop name for revenue transactions
            if clasificacion == "ingreso":
                # Get revenue types for validation
                revenue_types = await request_revenue_types(callback.message.chat.id)
                
                print(f"DEBUG: Regenerating formatted_response for crop sale")
                print(f"DEBUG: Selected crop_id: {crop_id}")
                print(f"DEBUG: Selected crop_name: {crop_name}")
                print(f"DEBUG: API response crop_variety before: {api_response.get('crop_variety')}")
                
                # Regenerate the formatted response with the correct crop name
                await process_revenue_classification(
                    callback.message, 
                    api_response, 
                    revenue_types or [], 
                    crop_varieties or [], 
                    selected_farm, 
                    respuesta
                )
                
                print(f"DEBUG: API response crop_variety after: {api_response.get('crop_variety')}")
                print(f"DEBUG: Formatted response: {api_response.get('formatted_response', 'NOT SET')}")
            
            # Final validation and processing
            await finalize_transaction(callback.message, api_response, clasificacion, respuesta, user_id)
        
        # Answer the callback
        await callback.answer(f"✅ Cultivo seleccionado: {crop_name}")
        
    except Exception as e:
        await callback.answer("❌ Error procesando la selección de cultivo.", show_alert=True)
        print(f"Error in crop selection callback: {e}") 