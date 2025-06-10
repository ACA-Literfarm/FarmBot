from aiogram.types import Message

async def cmd_help(message: Message):
    help_text = (
        "🤖 Comandos disponibles:\n"
        "/start - Mensaje de bienvenida\n"
        "/help - Mostrar este mensaje de ayuda\n"
        "/skip - Saltar campos opcionales como el cliente\n\n"
        "📋 Ejemplos de uso (El valor de la transacción no puede ser nulo ni negativo):\n"
        "• Para registrar compras: 'Hoy gasté 50 dólares en un 20 bolsas de fertilizante'\n"
        "• Para registrar ingresos: 'Hoy vendí 30 dólares de un paquete de 120 manzanas'\n\n"
        "✅ **Nuevo:** Ahora se requiere confirmación antes de registrar cualquier transacción.\n"
        "Recibirás botones de ✅ Confirmar o ❌ Cancelar para cada transacción."
    )
    await message.answer(help_text)