from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.session import AsyncSessionLocal
from shared.services.farm_selection_service import FarmSelectionService
from shared.services.chat_service import ChatSessionService
from shared.repositories.token_repository import TokenRepository
from shared.repositories.chat_repository import ChatSessionRepository
# from src.services.token_service import get_token_for_user TODO: Implement this function to retrieve the token for the user
from config import config
from shared.repositories.farm_repository import FarmRepository

# Dependency-injected services
farm_service = FarmSelectionService(
    repo_factory=FarmRepository,
    chat_session_repo_factory=ChatSessionRepository
)

chat_session_service = ChatSessionService(
    repo_factory=ChatSessionRepository
)

async def get_valid_token_for_chat(telegram_chat_id: int, session: AsyncSession):
    """Get a valid token for the given telegram chat ID."""
    try:
        chatRepo = ChatSessionRepository(session)
        tokenRepo = TokenRepository(session)
        chat_session = await chatRepo.get_chat_by_telegram_chat_id(telegram_chat_id)
        if chat_session is None:
            return None
        chat_session_id = chat_session.id
        tokens = await tokenRepo.get_valid_tokens_by_chat_session(chat_session_id)
        if tokens:
            return tokens[0].token  # Return the actual token string
        return None
    except Exception as e:
        print(f"Error getting valid token for chat {telegram_chat_id}: {e}")
        return None

async def farm_selection_callback(callback_query: types.CallbackQuery):
    if callback_query.message:
        telegram_chat_id = callback_query.message.chat.id
    else:
        # Use from_user.id as fallback when message is None
        telegram_chat_id = callback_query.from_user.id
    
    if callback_query.data is None:
        await callback_query.answer("❌ Invalid callback data.", show_alert=True)
        return
        
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

        token = await get_valid_token_for_chat(telegram_chat_id, db)
        if not token:
            if callback_query.message:
                await callback_query.message.answer("❌ No valid token found. Please log in again.")
            else:
                await callback_query.answer("❌ No valid token found. Please log in again.", show_alert=True)
            return

        try:
            await farm_service.select_farm(
                chat_id=telegram_chat_id,
                farm_id=selected_farm_id,
                litefarm_user_id=session.litefarm_user_id,
                token=token,
                session=db
            )
            if callback_query.message:
                await callback_query.message.answer("✅ Farm selected successfully.")
            else:
                await callback_query.answer("✅ Farm selected successfully.", show_alert=True)
        except ValueError as e:
            if callback_query.message:
                await callback_query.message.answer(f"❌ {str(e)}")
            else:
                await callback_query.answer(f"❌ {str(e)}", show_alert=True)
        except Exception as e:
            if callback_query.message:
                await callback_query.message.answer("🚨 An unexpected error occurred. Please try again.")
            else:
                await callback_query.answer("🚨 An unexpected error occurred. Please try again.", show_alert=True)
            # Optionally log error
            print(f"[ERROR] Farm selection failed: {e}")