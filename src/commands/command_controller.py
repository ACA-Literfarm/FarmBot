from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from handlers.regular_message import handle_regular_message, user_states, show_field_progress
from handlers.callback_handler import handle_confirmation_callback, handle_crop_selection_callback
from handlers.farm_handler import farm_selection_callback

from commands.start import cmd_start
from commands.help import cmd_help
from commands.login import cmd_login
from commands.cancel import cmd_cancel
from commands.disable_validation import cmd_deshabilitar_validacion
from commands.enable_validation import cmd_habilitar_validacion
from commands.farm_commands import clear_farm_command, select_farm_command, current_farm_command
from src.middleware.farm_validation import FarmValidationMiddleware

def register_handlers(dp: Dispatcher):
    """Register all message handlers with the dispatcher"""
    
    @dp.message(Command("start"))
    async def start_handler(message: Message):
        await cmd_start(message)

    @dp.message(Command("help"))
    async def help_handler(message: Message):
        await cmd_help(message)
    
    @dp.message(Command("login"))
    async def login_handler(message: Message):
        await cmd_login(message)
    
    @dp.message(Command("cancel"))
    async def cancel_handler(message: Message):
        await cmd_cancel(message)
    
    @dp.message(Command("deshabilitar_validacion"))
    async def deshabilitar_validacion_handler(message: Message):
        await cmd_deshabilitar_validacion(message)
    
    @dp.message(Command("habilitar_validacion"))
    async def habilitar_validacion_handler(message: Message):
        await cmd_habilitar_validacion(message)
    
    @dp.callback_query(lambda c: c.data and (c.data.startswith("confirm_") or c.data.startswith("cancel_")))
    async def confirmation_callback_handler(callback: CallbackQuery):
        await handle_confirmation_callback(callback)
        
    @dp.callback_query(lambda c: c.data and c.data.startswith("crop_"))
    async def crop_selection_callback_handler(callback: CallbackQuery):
        await handle_crop_selection_callback(callback)

    @dp.message(Command("selectfarm"))
    async def select_farm_handler(message: Message):
        await select_farm_command(message)

    @dp.message(Command("currentfarm"))
    async def cmd_current_farm_handler(message: Message):
        await current_farm_command(message)

    @dp.message(Command("clearfarm"))
    async def clear_farm_command_handler(message: Message):
        await clear_farm_command(message)

    @dp.message(Command("status"))
    async def status_handler(message: Message):
        await cmd_status(message)

    dp.callback_query.register(
        farm_selection_callback,
        lambda c: c.data
                  and
                  (c.data.startswith("select_farm:") or c.data == "remove_farm_selection")
                  )
    
    # Register middleware
    dp.message.middleware(FarmValidationMiddleware())

    # Regular message handler (should be last)
    dp.message.register(handle_regular_message)

async def cmd_status(message: Message):
    """
    Handle /status command to show current transaction progress.
    """
    if not message.from_user:
        await message.answer("❌ No se pudo identificar al usuario.")
        return
        
    user_id = message.from_user.id
    
    if user_id not in user_states:
        await message.answer(
            "ℹ️ **No hay transacción en progreso.**\n\n"
            "Para comenzar una nueva transacción, simplemente envía un mensaje describiendo tu gasto o ingreso.\n\n"
            "💡 **Ejemplos:**\n"
            "• \"Compré fertilizante por $500\"\n"
            "• \"Vendí 10 kg de tomates por $200\"\n"
            "• \"Pagué mano de obra $1000\""
        )
        return
    
    state = user_states[user_id]
    
    if not state.get("missing_fields"):
        await message.answer(
            "✅ **Transacción completa esperando confirmación.**\n\n"
            "Todos los campos han sido completados. La transacción está lista para ser procesada."
        )
        return
    
    # Show current progress
    await show_field_progress(message, user_id, state)
    
    # Show remaining fields
    missing_fields = state["missing_fields"]
    remaining_count = len(missing_fields)
    
    field_display_names = {
        "note": "📝 Descripción",
        "value": "💰 Valor/monto",
        "type": "📂 Tipo de transacción",
        "crop_variety": "🌱 Variedad de cultivo",
        "customer": "👤 Cliente",
        "quantity": "📊 Cantidad",
        "quantity_unit": "📏 Unidad de medida"
    }
    
    remaining_message = f"\n🔄 **Campos pendientes ({remaining_count}):**\n"
    for i, field in enumerate(missing_fields, 1):
        display_name = field_display_names.get(field, field)
        remaining_message += f"{i}. {display_name}\n"
    
    remaining_message += "\n💡 **Comandos disponibles:**\n"
    remaining_message += "• /cancel - Cancelar la transacción\n"
    remaining_message += "• /skip - Saltar campo opcional (solo cliente)\n"
    remaining_message += "• /status - Ver este estado nuevamente"
    
    await message.answer(remaining_message)