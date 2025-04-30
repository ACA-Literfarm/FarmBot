import os
import asyncio
import logging
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
load_dotenv()

# Set your bot token here or use an environment variable
BOT_TOKEN = os.getenv("TELEGRAM_API_KEY")
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("👋 Welcome to LiteFarmBot! Use /help to see available commands.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "🤖 Available commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "No command - Send message to deepseek for interpretation"
    )
    await message.answer(help_text)


@dp.message()
async def handle_no_command(message: Message):
    await message.answer("Message without command, sending to deepseek...")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
