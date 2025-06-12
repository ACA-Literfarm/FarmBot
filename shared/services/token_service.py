from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.models.token import Token
from shared.DTO.token.token_dto import TokenCreateDTO
from shared.interfaces.token_interface import ITokenRepository
from collections.abc import Callable

class TokenService:
    def __init__(self, repo_factory: Callable[[AsyncSession], ITokenRepository]):
        self._repo_factory = repo_factory

    async def create_token(
        self,
        dto: TokenCreateDTO,
        session: AsyncSession
    ) -> Token:
        repo = self._repo_factory(session)
        token = Token(**dto.model_dump())
        return await repo.create_token(token)

    async def get_active_token_by_chat(
        self,
        chat_session_id: int,
        session: AsyncSession
    ) -> list[Token]:
        repo = self._repo_factory(session)
        return list(await repo.get_valid_tokens_by_chat_session(chat_session_id))