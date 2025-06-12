from aiogram.types import Message

async def cmd_help(message: Message):
    help_text = (
        "🤖 **FarmBot - Asistente Financiero Agrícola**\n\n"
        "**Comandos disponibles:**\n"
        "/start - Iniciar el bot\n"
        "/help - Mostrar esta ayuda\n"
        "/login - Iniciar sesión en tu cuenta\n"
        "/selectfarm - Seleccionar granja activa\n"
        "/currentfarm - Ver granja actual\n"
        "/skip - Saltar mensaje actual\n\n"
        "**Gestión de granjas:**\n"
        "🏡 Usa /selectfarm para elegir con qué granja trabajar\n"
        "🟢 Usa /currentfarm para ver tu granja actual\n"
        "❌ Puedes quitar la selección de granja cuando quieras\n\n"
        "**Registro de transacciones:**\n"
        "💰 Simplemente escribe tus gastos e ingresos en lenguaje natural\n"
        "📊 El bot clasificará automáticamente tus transacciones\n"
        "🌱 Todas las transacciones se asocian a tu granja seleccionada\n\n"
        "**Ejemplos:**\n"
        '"Gasté 50 dólares en fertilizante"\n'
        '"Vendí tomates por 100 dólares a Juan Pérez"\n'
        '"Compré semillas por 25 dólares"\n\n'
        "¡Comienza seleccionando tu granja con /selectfarm! 🚀"
    )
    await message.answer(help_text, parse_mode='Markdown')