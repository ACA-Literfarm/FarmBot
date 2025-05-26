from aiogram.types import Message
from bot.state import user_states
from services.api_service import handle_api_transaction
from utils.typing_context import show_typing

async def cmd_skip(message: Message):
    """
    Handle /skip command to skip optional fields like customer.
    """
    user_id = message.from_user.id
    
    if user_id not in user_states:
        await message.answer("❌ No hay campos pendientes para completar.")
        return
    
    state = user_states[user_id]
    missing_fields = state["missing_fields"]
    
    if not missing_fields:
        await message.answer("❌ No hay campos pendientes para completar.")
        return
    
    current_field = missing_fields[0]
    
    # Only allow skipping customer field
    if current_field == "customer":
        # Skip this field by setting default value
        state["api_response"]["customer"] = "Cliente General"
        missing_fields.pop(0)
        
        if missing_fields:
            # Continue with next field
            next_field = missing_fields[0]
            if next_field == "value":
                await message.answer("💰 Por favor, ingresa el precio de la transacción:")
            elif next_field == "note":
                await message.answer("📝 Por favor, proporciona una breve descripción de la transacción:")
            elif next_field == "type":
                await message.answer("📂 Por favor, indica el tipo de transacción:")
        else:
            # All fields complete
            api_response = state["api_response"]
            del user_states[user_id]
            
            async with show_typing(message):
                await handle_api_transaction(api_response)
            
            await message.answer(f"{state['respuesta']}\n\n✅ Se usó 'Cliente General' como cliente.")
    else:
        await message.answer(f"❌ No puedes saltar el campo '{current_field}'. Es obligatorio.")