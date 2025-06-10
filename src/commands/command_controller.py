from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from handlers.regular_message import handle_regular_message
from handlers.callback_handler import handle_confirmation_callback
from commands.start import cmd_start
from commands.help import cmd_help
from commands.login import cmd_login
from commands.skip import cmd_skip

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
    
    @dp.message(Command("skip"))
    async def skip_handler(message: Message):
        await cmd_skip(message)

    @dp.callback_query(lambda c: c.data and (c.data.startswith("confirm_") or c.data.startswith("cancel_")))
    async def confirmation_callback_handler(callback: CallbackQuery):
        await handle_confirmation_callback(callback)

    @dp.message()
    async def handle_regular_message_wrapper(message: Message):
        await handle_regular_message(message)