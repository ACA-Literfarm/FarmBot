from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.models.chat_session import ChatSession
from shared.DTO.chat.chat_dto import ChatSessionCreateDTO
from shared.interfaces.chat_interface import IChatSessionRepository
from collections.abc import Callable

class ChatSessionService:
    def __init__(self, repo_factory: Callable[[AsyncSession], IChatSessionRepository]):
        self._repo_factory = repo_factory

    async def create_chat_session(
        self,
        dto: ChatSessionCreateDTO,
        session: AsyncSession
    ) -> ChatSession:
        repo = self._repo_factory(session)

        await repo.deactivate_all_chats_by_user_id(dto.litefarm_user_id)

        chat = ChatSession(
            litefarm_user_id=dto.litefarm_user_id,
            telegram_chat_id=dto.telegram_chat_id,
            is_active=True
        )

        return await repo.create_chat(chat)

    async def get_active_chat_by_telegram_id(
        self,
        telegram_chat_id: int,
        session: AsyncSession
    ) -> ChatSession | None:
        repo = self._repo_factory(session)
        chat = await repo.get_chat_by_telegram_chat_id(telegram_chat_id)
        return chat if chat and chat.is_active else None