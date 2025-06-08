from sqlalchemy.ext.asyncio import AsyncSession
from shared.DTO.user.user_dto import CreateUserDTO
from shared.db.models.user import User
from shared.interfaces.user_interface import IUserRepository
from collections.abc import Callable

class UserService:
    def __init__(self, repo_factory: Callable[[AsyncSession], IUserRepository]):
        self._repo_factory = repo_factory

    async def create_user(
        self, dto: CreateUserDTO, session: AsyncSession
    ) -> User:
        repo = self._repo_factory(session)

        existing = await repo.get_user_by_user_id(dto.litefarm_user_id)
        if existing:
            return existing

        user = User(**dto.model_dump())
        return await repo.create_user(user)

    async def user_exists(
        self, litefarm_user_id: str, session: AsyncSession
    ) -> bool:
        repo = self._repo_factory(session)
        user = await repo.get_user_by_user_id(litefarm_user_id)
        return user is not None
    