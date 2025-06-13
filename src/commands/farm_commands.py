from aiogram import types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.session import AsyncSessionLocal
from shared.services.farm_selection_service import FarmSelectionService
from shared.services.chat_service import ChatSessionService
# from src.services.token_service import get_token_for_user  # TODO: Implement this function to retrieve the token for the user
from config import config
from shared.repositories.farm_repository import FarmRepository
from shared.repositories.chat_repository import ChatSessionRepository

# Dependency-injected services
farm_service = FarmSelectionService(
    repo_factory=FarmRepository,
    chat_session_repo_factory=ChatSessionRepository
)

chat_session_service = ChatSessionService(
    repo_factory=ChatSessionRepository
)

async def select_farm_command(message: types.Message, state: FSMContext):
    telegram_chat_id = message.chat.id

    async with AsyncSessionLocal() as db:
        session = await chat_session_service.get_active_chat_by_telegram_id(
            telegram_chat_id=telegram_chat_id,
            session=db
        )

        if not session:
            await message.answer("⚠️ No active session. Please log in first.")
            return

        token = config.LOGIN_TOKEN or ""  # TODO: Replace with actual token retrieval logic
        farms = await farm_service.fetch_and_cache_farms(
            litefarm_user_id=session.litefarm_user_id,
            token=token,
            session=db
        )

        if not farms:
            await message.answer("❌ No farms found. Please create one in LiteFarm before continuing.")
            return

        buttons = [
            [types.InlineKeyboardButton(
                text=str(farm.name),
                callback_data=f"select_farm:{farm.litefarm_farm_id}"
            )]
            for farm in farms
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons, row_width=1)

        await message.answer("Please select one of your farms:", reply_markup=keyboard)


async def clear_farm_command(message: types.Message, state: FSMContext):
    telegram_chat_id = message.chat.id

    async with AsyncSessionLocal() as db:
        session = await chat_session_service.get_active_chat_by_telegram_id(
            telegram_chat_id=telegram_chat_id,
            session=db
        )

        if not session:
            await message.answer("No active session found. Please log in first.")
            return

        await farm_service.clear_farm_selection(chat_id=telegram_chat_id, session=db)
        await message.answer("✅ Farm selection has been cleared.")