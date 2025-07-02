from aiogram.types import Message
from commands.disable_validation import get_validation_enabled

async def cmd_help(message: Message):
    if not message.from_user:
        await message.answer("❌ No se pudo identificar al usuario.")
        return
        
    user_id = message.from_user.id
    validation_status = "✅ Habilitada" if get_validation_enabled(user_id) else "❌ Deshabilitada"
    
    help_text = (
        "🤖 <b>FarmBot - Asistente Financiero Agrícola</b>\n\n"
        "<b>Comandos disponibles:</b>\n"
        "/start - Iniciar el bot\n"
        "/ayuda - Mostrar este mensaje de ayuda\n"
        "/iniciar_sesion - Iniciar sesión en tu cuenta\n"
        "/seleccionar_granja - Seleccionar granja activa\n"
        "/granja_actual - Ver granja actual\n"
        "/borrar_seleccion_granja - Quitar selección de granja\n"
        "/estado - Ver progreso de transacción actual\n"
        "/skip - Saltar campo opcional (solo cliente)\n"
        "/cancelar - Cancelar transacción incompleta\n"
        "/deshabilitar_validacion - Deshabilitar confirmación de transacciones\n"
        "/habilitar_validacion - Habilitar confirmación de transacciones\n\n"
        f"⚙️ <b>Estado actual de validación:</b> {validation_status}\n\n"
        "<b>Gestión de granjas:</b>\n"
        "🏡 Usa /seleccionar_granja para elegir con qué granja trabajar\n"
        "🟢 Usa /granja_actual para ver tu granja actual\n"
        "❌ Puedes quitar la selección de granja cuando quieras\n\n"
        "<b>Registro de transacciones:</b>\n"
        "💰 Simplemente escribe tus gastos e ingresos en lenguaje natural\n"
        "📊 El bot clasificará automáticamente tus transacciones\n"
        "🌱 Todas las transacciones se asocian a tu granja seleccionada\n\n"
        "✅ <b>Características mejoradas:</b>\n"
        "• <b>Formulario interactivo:</b> Completa campos faltantes paso a paso\n"
        "• <b>Validación en tiempo real:</b> Errores claros con ejemplos\n"
        "• <b>Progreso visual:</b> Ve qué campos has completado\n"
        "• <b>Comando /estado:</b> Revisa el estado actual de tu transacción\n"
        "• <b>Selección de cultivos:</b> Botones para elegir cultivos disponibles\n"
        "• <b>Confirmación requerida</b> antes de registrar transacciones (configurable)\n"
        "• <b>Botones de ✅ Confirmar o ❌ Cancelar</b> para cada transacción\n"
        "• <b>Comando /cancelar</b> o botón ❌ Cancelar para transacciones incompletas\n"
        "• <b>Comandos para habilitar/deshabilitar</b> validación de confirmación\n\n"
        "<b>Ejemplos:</b>\n"
        "• 'Gasté 50 dólares en fertilizante'\n"
        "• 'Vendí tomates por 100 dólares a Juan Pérez'\n"
        "• 'Compré semillas por 25 dólares'\n"
        "• 'Hoy gasté 50 dólares en 20 bolsas de fertilizante'\n"
        "• 'Hoy vendí 30 dólares de un paquete de 120 manzanas'\n\n"
        "💡 <b>Consejo:</b> Si el bot te pide completar campos faltantes, puedes usar /estado para ver tu progreso actual.\n\n"
        "¡Comienza seleccionando tu granja con /seleccionar_granja! 🚀"
        )

    await message.answer(help_text, parse_mode='HTML')