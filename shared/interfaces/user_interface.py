from abc import ABC, abstractmethod
from uuid import UUID
from ..db.models.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def get_user_by_user_id(self, litefarm_user_id: UUID) -> User | None: ...

    @abstractmethod
    async def create_user(self, user: User) -> User: ...