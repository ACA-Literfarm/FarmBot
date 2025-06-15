from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.session import AsyncSessionLocal
from shared.services.farm_selection_service import FarmSelectionService
from shared.services.chat_service import ChatSessionService
from shared.repositories.farm_repository import FarmRepository
from shared.repositories.chat_repository import ChatSessionRepository
from config import config

class FarmValidationMiddleware(BaseMiddleware):
    """Middleware to ensure users have farms available and selected."""
    
    def __init__(self):
        self.farm_service = FarmSelectionService(
            repo_factory=FarmRepository,
            chat_session_repo_factory=ChatSessionRepository
        )
        self.chat_service = ChatSessionService(
            repo_factory=ChatSessionRepository
        )
        
        # Commands that DON'T require farm validation (exact command names)
        self.excluded_commands = {
            '/start', '/help', '/login', '/selectfarm', '/currentfarm', '/clearfarm'
        }
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
            
        # Skip validation for excluded commands (exact match)
        if event.text and event.text.strip() in self.excluded_commands:
            return await handler(event, data)
            
        # All other messages (including non-command messages) need farm validation
        # because they go through handle_regular_message which processes transactions
        needs_validation = True
        
        if not needs_validation:
            return await handler(event, data)
            
        telegram_chat_id = event.chat.id
        
        async with AsyncSessionLocal() as db:
            # Check if user has active session
            session = await self.chat_service.get_active_chat_by_telegram_id(
                telegram_chat_id=telegram_chat_id,
                session=db
            )
            
            if not session:
                await event.answer(
                    "❌ No tienes una sesión activa. Usa /start para comenzar."
                )
                return
                
            # Check if user has farms available
            token = config.LOGIN_TOKEN or ""
            farms = await self.farm_service.fetch_and_cache_farms(
                litefarm_user_id=str(session.litefarm_user_id),
                token=token,
                session=db
            )
            
            if not farms:
                await event.answer(
                    "❌ **No tienes granjas disponibles**\n\n"
                    "Para usar FarmBot necesitas:\n"
                    "1. Crear una granja en LiteFarm\n"
                    "2. Regresar aquí y usar /selectfarm\n\n"
                    "👆 **Acción requerida:** Crea una granja en LiteFarm para continuar.",
                    parse_mode='Markdown'
                )
                return
                
            # Check if user has selected a farm
            selected_farm = await self.farm_service.get_selected_farm(
                chat_id=telegram_chat_id,
                session=db
            )
            
            if not selected_farm:
                # Auto-select if only one farm
                if len(farms) == 1:
                    await self.farm_service.select_farm(
                        chat_id=telegram_chat_id,
                        farm_id=str(farms[0].litefarm_farm_id),
                        litefarm_user_id=str(session.litefarm_user_id),
                        token=token,
                        session=db
                    )
                    await event.answer(
                        f"✅ Se seleccionó automáticamente tu granja: **{farms[0].name}**",
                        parse_mode='Markdown'
                    )
                else:
                    await event.answer(
                        "❌ **Selecciona una granja primero**\n\n"
                        "Tienes múltiples granjas disponibles.\n"
                        "Usa /selectfarm para elegir una granja antes de continuar."
                    )
                    return
        
        return await handler(event, data)