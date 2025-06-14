from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from handlers.regular_message import handle_regular_message
from handlers.farm_handler import farm_selection_callback

from commands.start import cmd_start
from commands.help import cmd_help
from commands.login import cmd_login
from commands.farm_commands import clear_farm_command, select_farm_command, current_farm_command

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

    @dp.message(Command("selectfarm"))
    async def select_farm_handler(message: Message):
        await select_farm_command(message)

    @dp.message(Command("currentfarm"))
    async def cmd_current_farm_handler(message: Message):
        await current_farm_command(message)

    @dp.message(Command("clearfarm"))
    async def clear_farm_command_handler(message: Message):
        await clear_farm_command(message)

    dp.callback_query.register(
        farm_selection_callback,
        lambda c: c.data
                  and
                  (c.data.startswith("select_farm:") or c.data == "remove_farm_selection")
                  )
    
    # Regular message handler (should be last)
    dp.message.register(handle_regular_message)