from abc import ABC, abstractmethod
from typing import Optional, Sequence
from ..db.models.chat_session import ChatSession

class IChatSessionRepository(ABC):
    @abstractmethod
    async def get_chat_by_telegram_chat_id(self, telegram_chat_id: int) -> Optional[ChatSession]: ...

    @abstractmethod
    async def get_all_chats_by_user_id(self, litefarm_user_id: str) -> Sequence[ChatSession]: ...

    @abstractmethod
    async def create_chat(self, chat_session: ChatSession) -> ChatSession: ...

    @abstractmethod
    async def deactivate_all_chats_by_user_id(self, litefarm_user_id: str) -> None: ...