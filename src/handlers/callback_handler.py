from aiogram.types import CallbackQuery
from services.api_service import handle_api_transaction
from services.typing_context import show_typing
from handlers.regular_message import user_states

async def handle_confirmation_callback(callback: CallbackQuery):
    """
    Handle confirmation and cancellation callbacks.
    """
    try:
        # Parse callback data
        action, user_id_str = callback.data.split("_", 1)
        user_id = int(user_id_str)
        
        # Verify the callback is from the correct user
        if callback.from_user.id != user_id:
            await callback.answer("❌ Esta acción no es para ti.", show_alert=True)
            return
        
        # Check if user has pending confirmation
        if user_id not in user_states or not user_states[user_id].get("awaiting_confirmation"):
            await callback.answer("❌ No hay transacción pendiente de confirmación.", show_alert=True)
            return
        
        state = user_states[user_id]
        
        if action == "confirm":
            # Process the transaction
            api_response = state["api_response"]
            clasificacion = state["clasificacion"]
            
            # Clear user state
            del user_states[user_id]
            
            # Show typing while processing transaction
            async with show_typing(callback.message):
                await handle_api_transaction(api_response, clasificacion)
            
            # Update message with success response
            success_message = state["transaction_details"].replace("Voy a registrar", "¡Listo! He registrado")
            success_message += "\n\n✅ Transacción registrada exitosamente. Si tienes más gastos o ingresos para registrar, avísame."
            
            await callback.message.edit_text(success_message)
            await callback.answer("✅ Transacción registrada exitosamente!")
            
        elif action == "cancel":
            # Clear user state
            del user_states[user_id]
            
            # Update message to show cancellation
            await callback.message.edit_text("❌ Transacción cancelada. Puedes enviar otro mensaje para registrar una nueva transacción.")
            await callback.answer("❌ Transacción cancelada.")
            
    except Exception as e:
        await callback.answer("❌ Error procesando la confirmación.", show_alert=True)
        print(f"Error in confirmation callback: {e}") 