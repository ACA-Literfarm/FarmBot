from typing import Callable, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.models.farm import Farm
from shared.interfaces.farm_interface import IFarmRepository
from shared.interfaces.chat_interface import IChatSessionRepository
from shared.db.models.chat_session import ChatSession

class FarmSelectionService:
    def __init__(
        self,
        repo_factory: Callable[[AsyncSession], IFarmRepository],
        chat_session_repo_factory: Callable[[AsyncSession], IChatSessionRepository]
    ):
        self._repo_factory = repo_factory
        self._chat_session_repo_factory = chat_session_repo_factory

    async def fetch_and_cache_farms(
        self, 
        litefarm_user_id: str, 
        token: str, 
        session: AsyncSession
    ) -> List[Farm]:
        """
        Retrieve user farms from LiteFarm and cache locally.
        """
        farm_repo = self._repo_factory(session)
        farms = await farm_repo.get_user_farms_from_litefarm(
            litefarm_user_id=litefarm_user_id,
            token=token
        )
        return farms

    async def select_farm(
        self, 
        chat_id: int, 
        farm_id: str, 
        litefarm_user_id: str, 
        token: str, 
        session: AsyncSession
    ) -> None:
        """
        Set the selected farm for the user's active chat session.
        """
        farm_repo = self._repo_factory(session)
        is_valid = await farm_repo.is_farm_valid_for_user(
            farm_id=farm_id,
            litefarm_user_id=litefarm_user_id,
            token=token
        )

        if not is_valid:
            raise ValueError("Selected farm is not valid for this user.")

        await farm_repo.set_selected_farm(chat_id=chat_id, farm_id=farm_id)

    async def clear_farm_selection(
        self, 
        chat_id: int, 
        session: AsyncSession
    ) -> None:
        """
        Remove the selected farm from the user's active session.
        """
        farm_repo = self._repo_factory(session)
        await farm_repo.clear_selected_farm(chat_id=chat_id)

    async def get_selected_farm(self, chat_id: int, session: AsyncSession) -> Optional[Farm]:
        chat_repo = self._chat_session_repo_factory(session)
        farm_repo = self._repo_factory(session)

        chat_session = await chat_repo.get_chat_by_telegram_chat_id(chat_id)

        # If no chat session is found, create a new one
        if chat_session is None:
            chat_session = await chat_repo.create_chat(ChatSession(telegram_chat_id=chat_id))

        if chat_session is not None and getattr(chat_session, "selected_farm_id", None) is not None:
            return await farm_repo.get_farm_by_id(getattr(chat_session, "selected_farm_id"))
        return None