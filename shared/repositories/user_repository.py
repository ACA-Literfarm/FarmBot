from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..interfaces.user_interface import IUserRepository
from ..db.models.user import User

class UserRepository(IUserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_user_id(self, litefarm_user_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.litefarm_user_id == litefarm_user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user