from aiogram.types import Message

async def cmd_help(message: Message):
    help_text = (
        "🤖 Comandos disponibles:\n"
        "/start - Mensaje de bienvenida\n"
        "/help - Mostrar este mensaje de ayuda\n"
        "/cancel - Cancelar transacción incompleta\n\n"
        "📋 Ejemplos de uso (El valor de la transacción no puede ser nulo ni negativo):\n"
        "• Para registrar compras: 'Hoy gasté 50 dólares en un 20 bolsas de fertilizante'\n"
        "• Para registrar ingresos: 'Hoy vendí 30 dólares de un paquete de 120 manzanas'\n\n"
        "✅ **Características:**\n"
        "• Confirmación requerida antes de registrar transacciones\n"
        "• Botones de ✅ Confirmar o ❌ Cancelar para cada transacción\n"
        "• Comando /cancel o botón ❌ Cancelar para transacciones incompletas"
    )
    await message.answer(help_text)