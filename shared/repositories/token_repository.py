from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from datetime import datetime, timezone
from typing import Optional, Sequence

from ..interfaces.token_interface import ITokenRepository
from ..db.models.token import Token

class TokenRepository(ITokenRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_token(self, token_str: str) -> Optional[Token]:
        result = await self.db.execute(
            select(Token).where(Token.token == token_str)
        )
        return result.scalar_one_or_none()

    async def get_valid_tokens_by_chat_session(self, chat_session_id: int) -> Sequence[Token]:
        now = datetime.now(tz=timezone.utc)
        result = await self.db.execute(
            select(Token).where(
                Token.chat_session_id == chat_session_id,
                Token.expires_at > now,
                Token.is_active == True
            )
        )
        return result.scalars().all()

    async def create(self, token: Token) -> Token:
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def delete_expired(self) -> int:
        now = datetime.now(tz=timezone.utc)
        result = await self.db.execute(
            update(Token)
            .where(Token.expires_at <= now)
            .values(is_active=False)
            .returning(Token.id)
        )
        updated_ids = result.scalars().all()
        await self.db.commit()
        return len(updated_ids)

    async def delete_by_token(self, token_str: str) -> bool:
        result = await self.db.execute(
            update(Token)
            .where(Token.token == token_str)
            .values(is_active=False)
            .returning(Token.id)
        )
        updated_ids = result.scalars().all()
        await self.db.commit()
        return len(updated_ids) > 0

    async def update_token_for_chat(self, chat_session_id: int, new_token: Token) -> Token:
        await self.db.execute(
            update(Token)
            .where(Token.chat_session_id == chat_session_id)
            .values(is_active=False)
        )
        self.db.add(new_token)
        await self.db.commit()
        await self.db.refresh(new_token)
        return new_token