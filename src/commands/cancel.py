from aiogram.types import Message
from handlers.regular_message import user_states

async def cmd_cancel(message: Message):
    """Handle the /cancel command to cancel incomplete transactions"""
    user_id = message.from_user.id
    
    # Check if user has any pending state
    if user_id in user_states:
        # Clear the user state
        del user_states[user_id]
        await message.answer(
            "❌ Transacción cancelada exitosamente.\n\n"
            "Puedes enviar otro mensaje para registrar una nueva transacción. "
            "Si necesitas ayuda, escribe /ayuda para ver ejemplos de uso. 🚜"
        )
    else:
        await message.answer(
            "ℹ️ No tienes ninguna transacción pendiente para cancelar.\n\n"
            "Si quieres registrar un nuevo gasto o ingreso, simplemente envía un mensaje describiendo la transacción."
        )
