from aiogram.types import Message
from commands.disable_validation import set_validation_enabled

async def cmd_habilitar_validacion(message: Message):
    """Enable transaction confirmation validation for the user"""
    user_id = message.from_user.id
    set_validation_enabled(user_id, True)
    
    response_text = (
        "✅ **Validación de confirmación habilitada**\n\n"
        "Las transacciones requerirán confirmación antes de ser registradas.\n"
        "Para deshabilitar la validación, usa el comando /deshabilitar_validacion"
    )
    await message.answer(response_text)
