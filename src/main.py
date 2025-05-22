import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from bot.commands import cmd_start, cmd_help
from bot.handlers import cmd_login, handle_login_flow, handle_regular_message
from config import BOT_TOKEN
from fastapi import FastAPI
from routes.auth import router as auth_router  # Import the auth router

dp = Dispatcher()
#app = FastAPI()

# Register FastAPI routes
#app.include_router(auth_router)  # Add a prefix for API routes

# Register Telegram bot handlers
dp.message.register(cmd_start, Command("start"))
dp.message.register(cmd_help, Command("help"))
dp.message.register(cmd_login, Command("login"))
#dp.message.register(handle_login_flow)
dp.message.register(handle_regular_message)

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