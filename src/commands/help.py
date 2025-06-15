from aiogram.types import Message
from commands.disable_validation import get_validation_enabled

async def cmd_help(message: Message):
    user_id = message.from_user.id
    validation_status = "✅ Habilitada" if get_validation_enabled(user_id) else "❌ Deshabilitada"
    
    help_text = (
        "🤖 **FarmBot - Asistente Financiero Agrícola**\n\n"
        "**Comandos disponibles:**\n"
        "/start - Iniciar el bot\n"
        "/help - Mostrar este mensaje de ayuda\n"
        "/login - Iniciar sesión en tu cuenta\n"
        "/selectfarm - Seleccionar granja activa\n"
        "/currentfarm - Ver granja actual\n"
        "/clearfarm - Quitar selección de granja\n"
        "/skip - Saltar mensaje actual\n"
        "/cancel - Cancelar transacción incompleta\n"
        "/deshabilitar_validacion - Deshabilitar confirmación de transacciones\n"
        "/habilitar_validacion - Habilitar confirmación de transacciones\n\n"
        f"⚙️ **Estado actual de validación:** {validation_status}\n\n"
        "**Gestión de granjas:**\n"
        "🏡 Usa /selectfarm para elegir con qué granja trabajar\n"
        "🟢 Usa /currentfarm para ver tu granja actual\n"
        "❌ Puedes quitar la selección de granja cuando quieras\n\n"
        "**Registro de transacciones:**\n"
        "💰 Simplemente escribe tus gastos e ingresos en lenguaje natural\n"
        "📊 El bot clasificará automáticamente tus transacciones\n"
        "🌱 Todas las transacciones se asocian a tu granja seleccionada\n\n"
        "✅ **Características:**\n"
        "• Confirmación requerida antes de registrar transacciones (configurable)\n"
        "• Botones de ✅ Confirmar o ❌ Cancelar para cada transacción\n"
        "• Comando /cancel o botón ❌ Cancelar para transacciones incompletas\n"
        "• Comandos para habilitar/deshabilitar validación de confirmación\n\n"
        "**Ejemplos:**\n"
        "• 'Gasté 50 dólares en fertilizante'\n"
        "• 'Vendí tomates por 100 dólares a Juan Pérez'\n"
        "• 'Compré semillas por 25 dólares'\n"
        "• 'Hoy gasté 50 dólares en 20 bolsas de fertilizante'\n"
        "• 'Hoy vendí 30 dólares de un paquete de 120 manzanas'\n\n"
        "¡Comienza seleccionando tu granja con /selectfarm! 🚀"
        )

    await message.answer(help_text, parse_mode='Markdown')