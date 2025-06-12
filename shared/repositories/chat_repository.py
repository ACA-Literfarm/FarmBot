from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, Sequence

from ..interfaces.chat_interface import IChatSessionRepository
from ..db.models.chat_session import ChatSession

class ChatSessionRepository(IChatSessionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_chat_by_telegram_chat_id(self, telegram_chat_id: int) -> Optional[ChatSession]:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.telegram_chat_id == telegram_chat_id)
        )
        return result.scalar_one_or_none()

    async def get_all_chats_by_user_id(self, litefarm_user_id: str) -> Sequence[ChatSession]:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.litefarm_user_id == litefarm_user_id)
        )
        return result.scalars().all()

    async def create_chat(self, chat_session: ChatSession) -> ChatSession:
        self.db.add(chat_session)
        await self.db.flush()
        await self.db.refresh(chat_session)
        return chat_session

    async def deactivate_all_chats_by_user_id(self, litefarm_user_id: str) -> None:
        await self.db.execute(
            update(ChatSession)
            .where(ChatSession.litefarm_user_id == litefarm_user_id)
            .values(is_active=False)
            .execution_options(synchronize_session=False)
        )
        await self.db.flush()