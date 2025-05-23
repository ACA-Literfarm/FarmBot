from aiogram.types import Message

async def cmd_help(message: Message):
    help_text = (
        "🤖 Comandos disponibles:\n"
        "/start - Mensaje de bienvenida\n"
        "/help - Mostrar este mensaje de ayuda\n"
        "/login - Iniciar sesión en tu cuenta\n"
        "/revenue_types - Obtener tipos de ingresos\n"
        "/crop_varieties - Obtener variedades de cultivos\n"
        "/cache_info - Información del caché de variedades de cultivos\n"
        "/clear_cache - Limpiar el caché de variedades de cultivos\n\n"
        "📋 Ejemplos de uso:\n"
        "• Para registrar compras: 'Hoy gasté 50 dólares en un 20 bolsas de fertilizante'\n"
        "• Para registrar ingresos: 'Hoy vendí 30 dólares de un paquete de 120 manzanas'\n"
    )
    await message.answer(help_text)