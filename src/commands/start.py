from aiogram.types import Message

async def cmd_start(message: Message):
    await message.answer("👋 ¡Bienvenido a LiteFarmBot! Usa /ayuda para ver los comandos disponibles.")