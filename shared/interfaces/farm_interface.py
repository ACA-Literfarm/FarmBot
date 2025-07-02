# shared/interfaces/farm_repository_interface.py
from abc import ABC, abstractmethod
from typing import Optional, Sequence
from ..db.models.chat_session import ChatSession
from typing import List
from ..db.models.farm import Farm


class IFarmRepository(ABC):
    
    @abstractmethod
    async def get_user_farms_from_litefarm(self, litefarm_user_id: str, token: str) -> List[Farm]: ...

    @abstractmethod
    async def set_selected_farm(self, chat_id, farm_id) -> None: ...

    @abstractmethod
    async def clear_selected_farm(self, chat_id) -> None: ...

    @abstractmethod
    async def is_farm_valid_for_user(self, token, farm_id, litefarm_user_id) -> bool : ...

    @abstractmethod
    async def get_farm_by_id(self, farm_id: str) -> Optional[Farm]: ...