import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import bot.commands as commands
import bot.handlers as handlers
from config import BOT_TOKEN
from fastapi import FastAPI
from routes.auth import router as auth_router  # Import the auth router
from bot.commands.cache import cmd_cache_info, cmd_clear_cache  # Import cache commands

dp = Dispatcher()
#app = FastAPI()

# Register FastAPI routes
#app.include_router(auth_router)  # Add a prefix for API routes

# Register Telegram bot handlers
dp.message.register(commands.cmd_start, Command("start"))
dp.message.register(commands.cmd_help, Command("help"))
dp.message.register(commands.cmd_login, Command("login"))
dp.message.register(commands.cmd_revenue_types, Command("revenue_types"))
dp.message.register(commands.cmd_crop_varieties, Command("crop_varieties"))  # Register the new command
dp.message.register(commands.cmd_cache_info, Command("cache_info"))
dp.message.register(commands.cmd_clear_cache, Command("clear_cache"))

dp.message.register(handlers.handle_regular_message)
# dp.message.register(handle_login_flow, state="*")  # Register the login flow handler

async def main() -> None:
    if BOT_TOKEN is None:
        raise ValueError("BOT_TOKEN must not be None")
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())