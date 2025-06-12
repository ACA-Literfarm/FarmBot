from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from handlers.regular_message import handle_regular_message
from commands.start import cmd_start
from commands.help import cmd_help
from commands.login import cmd_login
from commands.current_farm import cmd_current_farm
from commands.select_farm import cmd_select_farm, handle_farm_selection_callback

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

    dp.message.register(cmd_select_farm, Command("selectfarm"))
    dp.message.register(cmd_current_farm, Command("currentfarm"))
    

    @dp.message()
    async def handle_regular_message_wrapper(message: Message):
        await handle_regular_message(message)

    # Callback query handlers for inline keyboards
    dp.callback_query.register(handle_farm_selection_callback, lambda c: c.data and (c.data.startswith("select_farm:") or c.data == "remove_farm_selection"))
    
    # Regular message handler (should be last)
    dp.message.register(handle_regular_message)