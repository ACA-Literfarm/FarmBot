from abc import ABC, abstractmethod
from typing import Optional, Sequence
from ..db.models.token import Token

class ITokenRepository(ABC):
    @abstractmethod
    async def get_by_token(self, token_str: str) -> Optional[Token]: ...

    @abstractmethod
    async def get_valid_tokens_by_chat_session(self, chat_session_id: int) -> Sequence[Token]: ...

    @abstractmethod
    async def create(self, token: Token) -> Token: ...

    @abstractmethod
    async def delete_expired(self) -> int: ...

    @abstractmethod
    async def delete_by_token(self, token_str: str) -> bool: ...

    @abstractmethod
    async def update_token_for_chat(self, chat_session_id: int, new_token: Token) -> Token: ...