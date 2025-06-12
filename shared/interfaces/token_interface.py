from abc import ABC, abstractmethod
from typing import Optional, Sequence
from ..db.models.token import Token

class ITokenRepository(ABC):
    @abstractmethod
    async def get_token_by_token_string(self, token_str: str) -> Optional[Token]: ...

    @abstractmethod
    async def get_valid_tokens_by_chat_session(self, chat_session_id: int) -> Sequence[Token]: ...

    @abstractmethod
    async def create_token(self, token: Token) -> Token: ...

    @abstractmethod
    async def deactivate_expired_tokens(self) -> int: ...

    @abstractmethod
    async def deactivate_token_by_token_string(self, token_str: str) -> bool: ...

    @abstractmethod
    async def update_token_for_chat(self, chat_session_id: int, new_token: Token) -> Token: ...