from aiogram.types import Message

# Global storage for user validation preferences
user_validation_settings = {}

def get_validation_enabled(user_id: int) -> bool:
    """Get validation setting for a user (default is True)"""
    return user_validation_settings.get(user_id, True)

def set_validation_enabled(user_id: int, enabled: bool):
    """Set validation setting for a user"""
    user_validation_settings[user_id] = enabled

async def cmd_deshabilitar_validacion(message: Message):
    """Disable transaction confirmation validation for the user"""
    user_id = message.from_user.id
    set_validation_enabled(user_id, False)
    
    response_text = (
        "✅ **Validación de confirmación deshabilitada**\n\n"
        "Las transacciones se registrarán automáticamente sin confirmación.\n"
        "Para volver a habilitar la validación, usa el comando /habilitar_validacion"
    )
    await message.answer(response_text)
