from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, insert
from datetime import datetime, timezone
from typing import Optional, Sequence, List

from src.services.api_service import request_user_farms
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..db.models.farm import Farm
from ..db.models.chat_session import ChatSession 
from ..interfaces.farm_interface import IFarmRepository

class FarmRepository(IFarmRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_farms_from_litefarm(
            self, 
            litefarm_user_id: str = "771015ac-322e-11f0-94b4-66ab45519382",
            token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzcxMDE1YWMtMzIyZS0xMWYwLTk0YjQtNjZhYjQ1NTE5MzgyIiwiaWF0IjoxNzQ5MDg1MDY2LCJleHAiOjE3NDk2ODk4NjZ9.vPYhOPjJlOdVsbKIk2a0jKTWdq4P6qns01Xg8ewhw-Q", 
            ) -> List[Farm]:
        # TODO: Remove hardcoded values
        farms_data = await request_user_farms(token=token, userId=litefarm_user_id) 
        if not farms_data:
            return []

        result = []
        for farm_dict in farms_data:
            farm = Farm(
                litefarm_farm_id=farm_dict['farm_id'],
                name=farm_dict['farm_name'],
            )

            # Upsert to avoid duplicates (if farm already exists)
            stmt = pg_insert(Farm).values(
                litefarm_farm_id=farm.litefarm_farm_id,
                name=farm.name
            ).on_conflict_do_nothing(index_elements=['litefarm_farm_id'])

            await self.db.execute(stmt)
            result.append(farm)

        await self.db.commit()
        return result

    async def set_selected_farm(self, chat_id, farm_id) -> None:
        stmt = (
            update(ChatSession)
            .where(ChatSession.telegram_chat_id == chat_id)
            .where(ChatSession.is_active.is_(True))
            .values(selected_farm_id=farm_id)
        )
        result = await self.db.execute(stmt)

        if result.rowcount == 0:
            raise ValueError(f"No active session found for chat_id {chat_id}")

        await self.db.commit()

    async def clear_selected_farm(self, chat_id) -> None:
        stmt = (
            update(ChatSession)
            .where(ChatSession.telegram_chat_id == chat_id)
            .where(ChatSession.is_active.is_(True))
            .values(selected_farm_id=None)
        )
        result = await self.db.execute(stmt)

        if result.rowcount == 0:
            raise ValueError(f"No active session found to clear farm for chat_id {chat_id}")

        await self.db.commit()

    async def is_farm_valid_for_user(self, token, farm_id, litefarm_user_id) -> bool:
        farms_data = await request_user_farms(token=token, userId=litefarm_user_id)
        if not farms_data:
            return False

        return any(f["farm_id"] == farm_id for f in farms_data)
    
    async def get_farm_by_id(self, farm_id: str) -> Optional[Farm]:
        stmt = select(Farm).where(Farm.litefarm_farm_id == farm_id)
        result = await self.db.execute(stmt)
        farm = result.scalars().first()
        return farm if farm else None