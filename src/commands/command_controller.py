from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from handlers.regular_message import handle_regular_message
from commands.start import cmd_start
from commands.help import cmd_help
from commands.login import cmd_login

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


    @dp.message()
    async def handle_regular_message_wrapper(message: Message):
        await handle_regular_message(message)