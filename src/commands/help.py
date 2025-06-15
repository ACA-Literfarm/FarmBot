from aiogram.types import Message
from commands.disable_validation import get_validation_enabled

async def cmd_help(message: Message):
    user_id = message.from_user.id
    validation_status = "✅ Habilitada" if get_validation_enabled(user_id) else "❌ Deshabilitada"
    
    help_text = (
        "🤖 Comandos disponibles:\n"
        "/start - Mensaje de bienvenida\n"
        "/help - Mostrar este mensaje de ayuda\n"
        "/cancel - Cancelar transacción incompleta\n"
        "/deshabilitar_validacion - Deshabilitar confirmación de transacciones\n"
        "/habilitar_validacion - Habilitar confirmación de transacciones\n\n"
        f"⚙️ **Estado actual de validación:** {validation_status}\n\n"
        "📋 Ejemplos de uso (El valor de la transacción no puede ser nulo ni negativo):\n"
        "• Para registrar compras: 'Hoy gasté 50 dólares en un 20 bolsas de fertilizante'\n"
        "• Para registrar ingresos: 'Hoy vendí 30 dólares de un paquete de 120 manzanas'\n\n"
        "✅ **Características:**\n"
        "• Confirmación requerida antes de registrar transacciones (configurable)\n"
        "• Botones de ✅ Confirmar o ❌ Cancelar para cada transacción\n"
        "• Comando /cancel o botón ❌ Cancelar para transacciones incompletas\n"
        "• Comandos para habilitar/deshabilitar validación de confirmación"
    )
    await message.answer(help_text)