from aiogram.types import CallbackQuery, Message
from services.api_service import handle_api_transaction
from services.typing_context import show_typing
from handlers.regular_message import user_states

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
        
        if len(callback_parts) == 3 and callback_parts[1] == "incomplete":
            # Handle incomplete transaction cancellation (format: cancel_incomplete_userID)
            user_id = int(callback_parts[2])
        elif len(callback_parts) == 3 and callback_parts[1] == "transaction":
            # Handle transaction confirmation/cancellation (format: confirm_transaction_userID or cancel_transaction_userID)
            user_id = int(callback_parts[2])
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
                        "Si necesitas ayuda, escribe /help para ver ejemplos de uso. 🚜"
                    )
                except Exception:
                    await callback.message.answer(
                        "❌ Transacción cancelada exitosamente.\n\n"
                        "Puedes enviar otro mensaje para registrar una nueva transacción. "
                        "Si necesitas ayuda, escribe /help para ver ejemplos de uso. 🚜"
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