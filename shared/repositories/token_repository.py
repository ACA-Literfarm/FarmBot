from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from datetime import datetime, timezone
from typing import Optional, Sequence

from ..interfaces.token_interface import ITokenRepository
from ..db.models.token import Token

class TokenRepository(ITokenRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_token_by_token_string(self, token_str: str) -> Optional[Token]:
        result = await self.db.execute(
            select(Token).where(Token.token == token_str)
        )
        return result.scalar_one_or_none()

    async def get_valid_tokens_by_chat_session(self, chat_session_id: int) -> Sequence[Token]:
        # Ensure chat_session_id is a valid integer
        chat_session_id = int(chat_session_id)
        # Now get only valid tokens
        result = await self.db.execute(
            select(Token).where(
                Token.chat_session_id == chat_session_id,
                Token.is_active == True
            )
        )
        valid_tokens = result.scalars().all()
        
        return valid_tokens


    async def create_token(self, token: Token) -> Token:
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token

    async def deactivate_expired_tokens(self) -> int:
        now = datetime.now(tz=timezone.utc)
        result = await self.db.execute(
            update(Token)
            .where(Token.expires_at <= now)
            .values(is_active=False)
            .execution_options(synchronize_session=False)
            .returning(Token.id)
        )
        updated_ids = result.scalars().all()
        await self.db.flush()
        return len(updated_ids)

    async def deactivate_token_by_token_string(self, token_str: str) -> bool:
        result = await self.db.execute(
            update(Token)
            .where(Token.token == token_str)
            .values(is_active=False)
            .execution_options(synchronize_session=False)
            .returning(Token.id)
        )
        updated_ids = result.scalars().all()
        await self.db.flush()
        return len(updated_ids) > 0

    async def update_token_for_chat(self, chat_session_id: int, new_token: Token) -> Token:
        await self.db.execute(
            update(Token)
            .where(Token.chat_session_id == chat_session_id)
            .values(is_active=False)
            .execution_options(synchronize_session=False)
        )
        self.db.add(new_token)
        await self.db.flush()
        await self.db.refresh(new_token)
        return new_token