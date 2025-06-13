from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.session import AsyncSessionLocal
from shared.services.farm_selection_service import FarmSelectionService
from shared.services.chat_service import ChatSessionService
# from src.services.token_service import get_token_for_user TODO: Implement this function to retrieve the token for the user
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

async def farm_selection_callback(callback_query: types.CallbackQuery):
    telegram_chat_id = callback_query.message.chat.id
    data = callback_query.data.split(":")
    
    if len(data) != 2 or not data[1]:
        await callback_query.answer("❌ Invalid farm selection.", show_alert=True)
        return

    selected_farm_id = data[1]

    async with AsyncSessionLocal() as db:
        session = await chat_session_service.get_active_chat_by_telegram_id(
            telegram_chat_id=telegram_chat_id,
            session=db
        )

        if not session:
            if callback_query.message:
                await callback_query.message.answer("⚠️ No active session found. Please log in.")
            else:
                await callback_query.answer("⚠️ No active session found. Please log in.", show_alert=True)
            return

        token = config.LOGIN_TOKEN or ""  # TODO: Replace with actual token retrieval logic

        try:
            await farm_service.select_farm(
                chat_id=telegram_chat_id,
                farm_id=selected_farm_id,
                litefarm_user_id=session.litefarm_user_id,
                token=token,
                session=db
            )
            await callback_query.message.answer("✅ Farm selected successfully.")
        except ValueError as e:
            await callback_query.message.answer(f"❌ {str(e)}")
        except Exception as e:
            await callback_query.message.answer("🚨 An unexpected error occurred. Please try again.")
            # Optionally log error
            print(f"[ERROR] Farm selection failed: {e}")