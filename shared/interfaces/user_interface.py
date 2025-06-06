from abc import ABC, abstractmethod
from uuid import UUID
from ..db.models.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, litefarm_user_id: UUID) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...