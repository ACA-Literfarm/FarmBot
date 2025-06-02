import asyncio
from contextlib import asynccontextmanager
from aiogram.types import Message
from aiogram.enums import ChatAction

@asynccontextmanager
async def show_typing(message: Message, interval: float = 4.0):
    """
    Context manager that shows typing indicator while processing.
    
    Args:
        message: The message object to respond to
        interval: How often to refresh the typing action (Telegram expires it after 5 seconds)
    """
    typing_task = asyncio.create_task(_keep_typing(message, interval))
    
    try:
        yield
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass

async def _keep_typing(message: Message, interval: float):
    """Continuously send typing action."""
    if not message.bot:
        return
        
    while True:
        try:
            await message.bot.send_chat_action(
                chat_id=message.chat.id, 
                action=ChatAction.TYPING
            )
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break
        except Exception:
            # Don't break on errors, just continue
            await asyncio.sleep(interval)