from aiogram.types import Message
from bot.state import user_states

async def cmd_login(message: Message):
    """
    Handles the /login command to initiate the login process.
    """
    if message.from_user is None:
        await message.answer("⚠️ No se pudo identificar al usuario. Por favor, intenta nuevamente.")
        return
    user_id = message.from_user.id
    user_states[user_id] = {"state": "awaiting_username"}
    await message.answer("📝 Por favor, ingresa tu nombre de usuario:")