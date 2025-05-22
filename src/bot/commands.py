from aiogram.filters import Command
from aiogram.types import Message
from bot.handlers import cmd_login, handle_login_flow

async def cmd_start(message: Message):
    await message.answer("👋 ¡Bienvenido a LiteFarmBot! Usa /help para ver los comandos disponibles.")

async def cmd_help(message: Message):
    help_text = (
        "🤖 Comandos disponibles:\n"
        "/start - Mensaje de bienvenida\n"
        "/help - Mostrar este mensaje de ayuda\n"
        "/login - Iniciar sesión en tu cuenta\n"
        "/revenue_types - Obtener tipos de ingresos\n"
        "/crop_varieties - Obtener variedades de cultivos\n"
        "📋 Ejemplos de uso:\n"
        "• Para registrar compras: 'Hoy gasté 50 dólares en un 20 bolsas de fertilizante'\n"
        "• Para registrar ingresos: 'Hoy vendí 30 dólares de un paquete de 120 manzanas'\n"
    )
    await message.answer(help_text)