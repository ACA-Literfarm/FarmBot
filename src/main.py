import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher 
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from commands.command_controller import register_handlers
from config import config

# Validate that all required environment variables are set
config.validate_required_vars()

# Initialize the bot and dispatcher
dp = Dispatcher()

# Register all message handlers
register_handlers(dp)

async def main() -> None:
    bot = Bot(token=config.TELEGRAM_API_KEY, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

