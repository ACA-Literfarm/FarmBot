from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.session import AsyncSessionLocal

from shared.repositories.user_repository import UserRepository
from shared.repositories.chat_repository import ChatSessionRepository
from shared.repositories.token_repository import TokenRepository


class UnitOfWork:
    def __init__(self):
        self.session: AsyncSession = None
        self.user_repo: UserRepository = None
        self.chat_repo: ChatSessionRepository = None
        self.token_repo: TokenRepository = None

    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        self.user_repo = UserRepository(self.session)
        self.chat_repo = ChatSessionRepository(self.session)
        self.token_repo = TokenRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()