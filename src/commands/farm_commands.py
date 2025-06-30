from aiogram import types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.session import AsyncSessionLocal
from shared.services.farm_selection_service import FarmSelectionService
from shared.services.chat_service import ChatSessionService
from shared.services.user_service import UserService
from shared.repositories.token_repository import TokenRepository
from shared.repositories.chat_repository import ChatSessionRepository
# from src.services.token_service import get_token_for_user  # TODO: Implement this function to retrieve the token for the user
from config import config
from shared.repositories.farm_repository import FarmRepository
from shared.repositories.user_repository import UserRepository
from shared.DTO.chat.chat_dto import ChatSessionCreateDTO
from shared.DTO.user.user_dto import CreateUserDTO

import logging
from aiogram.types import Message
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dependency-injected services
farm_service = FarmSelectionService(
    repo_factory=FarmRepository,
    chat_session_repo_factory=ChatSessionRepository
)

chat_session_service = ChatSessionService(
    repo_factory=ChatSessionRepository
)

user_service = UserService(
    repo_factory=UserRepository
)

async def get_valid_token_for_chat(telegram_chat_id: int, session: AsyncSession):
    """Get a valid token for the given telegram chat ID."""
    try:
        chatRepo = ChatSessionRepository(session)
        tokenRepo = TokenRepository(session)
        chat_session = await chatRepo.get_chat_by_telegram_chat_id(telegram_chat_id)
        if chat_session is None:
            return None
        chat_session_id = chat_session.id
        tokens = await tokenRepo.get_valid_tokens_by_chat_session(chat_session_id)
        if tokens:
            return tokens[0].token  # Return the actual token string
        return None
    except Exception as e:
        print(f"Error getting valid token for chat {telegram_chat_id}: {e}")
        return None

async def select_farm_command(message: types.Message):
    telegram_chat_id = message.chat.id

    async with AsyncSessionLocal() as db:
        logger.info(f"Received /selectfarm command from chat ID: {telegram_chat_id}")

        session = await chat_session_service.get_active_chat_by_telegram_id(
            telegram_chat_id=telegram_chat_id,
            session=db
        )

        logger.info(f"Retrieved session for chat ID {telegram_chat_id}: {session}")

        if not session:
            # If no active session, you might want to redirect to login or handle it accordingly
            # For now, we will create the session if it doesn't exist

            logger.info(f"No active session found for chat ID {telegram_chat_id}. Creating new session.")

            litefarm_user_id = config.LITEFARM_USER_ID if config.LITEFARM_USER_ID else ""

            user = await user_service.user_exists(
                litefarm_user_id=litefarm_user_id,  # TODO: Replace with actual user ID retrieval logic
                session=db
            )

            if not user:
                await user_service.create_user(
                    CreateUserDTO(
                        litefarm_user_id=litefarm_user_id,  # TODO: Replace with actual user ID retrieval logic
                    ),
                    session=db
                )

            session = await chat_session_service.create_chat_session(
                dto=ChatSessionCreateDTO(
                    litefarm_user_id=litefarm_user_id,  # TODO: Replace with actual user ID retrieval logic
                    telegram_chat_id=telegram_chat_id
                ),
                session=db
            )

        token = await get_valid_token_for_chat(telegram_chat_id, db)
        if not token:
            await message.answer("❌ No valid token found. Please log in again using /iniciar_sesion.")
            return
            
        farms = await farm_service.fetch_and_cache_farms(
            litefarm_user_id=str(session.litefarm_user_id),
            token=token,
            session=db
        )

        if not farms:
            await message.answer(
                "❌ <b>No tienes granjas disponibles</b>\n\n"
                "Para usar FarmBot necesitas crear una granja en LiteFarm primero.\n\n"
                "📋 <b>Pasos a seguir:</b>\n"
                "1. Ve a LiteFarm y crea una nueva granja\n"
                "2. Regresa aquí y usa /seleccionar_granja nuevamente\n\n"
                "ℹ️ Sin una granja no podrás registrar transacciones.",
                parse_mode='HTML'
            )
            return

        # Auto-select if only one farm
        if len(farms) == 1:
            try:
                await farm_service.select_farm(
                    chat_id=telegram_chat_id,
                    farm_id=str(farms[0].litefarm_farm_id),
                    litefarm_user_id=str(session.litefarm_user_id),
                    token=token,
                    session=db
                )
                await message.answer(
                    f"✅ <b>Granja seleccionada automáticamente</b>\n\n"
                    f"🏡 <b>{farms[0].name}</b>\n\n"
                    "Ya puedes empezar a registrar transacciones.",
                    parse_mode='HTML'
                )
                return
            except Exception as e:
                logger.error(f"Error auto-selecting farm: {e}")

        buttons = [
            [types.InlineKeyboardButton(
                text=str(farm.name),
                callback_data=f"select_farm:{farm.litefarm_farm_id}"
            )]
            for farm in farms
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons, row_width=1)

        await message.answer(
            "🏡 <b>Selecciona una granja:</b>\n\n"
            "Elige la granja donde quieres registrar tus transacciones:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )


async def clear_farm_command(message: Message):
    telegram_chat_id = message.chat.id

    async with AsyncSessionLocal() as db:
        session = await chat_session_service.get_active_chat_by_telegram_id(
            telegram_chat_id=telegram_chat_id,
            session=db
        )

        if not session:
            await message.answer("No active session found. Please log in first.")
            return

        await farm_service.clear_farm_selection(chat_id=telegram_chat_id, session=db)
        await message.answer("✅ Selección de granja borrada, debes seleccionar una granja para poder registrar ingresos o gastos.")

async def current_farm_command(message: Message) -> None:
    """
    Handle /currentfarm command to show currently selected farm.
    """
    telegram_chat_id = message.chat.id

    try:
        async with AsyncSessionLocal() as db:
            current_farm = await farm_service.get_selected_farm(chat_id=telegram_chat_id, session=db)

            if current_farm:
                await message.answer(
                    f"🟢 <b>Granja actual:</b> {current_farm.name}\n\n"
                    f"Todas las transacciones se registrarán en esta granja.\n"
                    f"Usa /seleccionar_granja para cambiar de granja.",
                    parse_mode='HTML'
                )
            else:
                await message.answer(
                    "❌ No tienes ninguna granja seleccionada.\n\n"
                    "Usa /seleccionar_granja para elegir una granja antes de registrar transacciones."
                )

    except Exception as e:
        logging.error(f"Error in cmd_current_farm: {e}")
        await message.answer(
            "❌ Ocurrió un error al obtener la información de tu granja actual."
        )