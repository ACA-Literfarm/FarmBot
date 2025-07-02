import asyncio
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from shared.db.session import AsyncSessionLocal

from shared.services.chat_service import ChatSessionService
from shared.DTO.chat.chat_dto import ChatSessionCreateDTO
from shared.services.token_service import TokenService
from shared.DTO.token.token_dto import TokenCreateDTO
from shared.services.user_service import UserService
from shared.DTO.user.user_dto import CreateUserDTO

from shared.repositories.user_repository import UserRepository
from shared.repositories.chat_repository import ChatSessionRepository
from shared.repositories.token_repository import TokenRepository
from shared.DTO.token.token_return_dto import TokenOutDTO
from shared.DTO.chat.chat_return_dto import ChatSessionOutDTO
from shared.DTO.user.user_return_dto import UserOutDTO

# Services (now with injected repo factories)
user_service = UserService(repo_factory=UserRepository)
chat_service = ChatSessionService(repo_factory=ChatSessionRepository)
token_service = TokenService(repo_factory=TokenRepository)

def check_response(data, label=""):
    print(f"✅ {label} Success:", data)

def handle_error(e, label=""):
    print(f"❌ {label} Error: {e}")

# --- Functional Tests ---

async def test_create_chat_session_success(session):
    print("\n=== Test: Create Chat Session Successfully ===")

    user_id = uuid4()
    telegram_chat_id = int(uuid4().int % 1_000_000_000_000)

    try:
        async with session.begin():
            user = await user_service.create_user(
                CreateUserDTO(litefarm_user_id=user_id),
                session=session
            )
            check_response(UserOutDTO.model_validate(user), "User creation")

            chat = await chat_service.create_chat_session(
                ChatSessionCreateDTO(
                    litefarm_user_id=user_id,
                    telegram_chat_id=telegram_chat_id
                ),
                session=session
            )
            check_response(ChatSessionOutDTO.model_validate(chat), "Chat session creation")
            return chat.id, telegram_chat_id

    except IntegrityError as e:
        handle_error(e, "Create Chat Session")
        return None, None

async def test_get_active_chat_session(session, telegram_chat_id: int):
    print("\n=== Test: Get Active Chat Session ===")
    try:
        async with session.begin():
            chat = await chat_service.get_active_chat_by_telegram_id(telegram_chat_id, session=session)
            if chat:
                check_response(ChatSessionOutDTO.model_validate(chat), "Get active chat session")
            else:
                print("❌ No active chat session found")
    except Exception as e:
        handle_error(e, "Get active chat session")

async def test_create_token_success(session, chat_session_id: int):
    print("\n=== Test: Create Token Successfully ===")
    token_str = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    try:
        async with session.begin():
            token = await token_service.create_token(
                TokenCreateDTO(
                    chat_session_id=chat_session_id,
                    token=token_str,
                    expires_at=expires_at
                ),
                session=session
            )
            check_response(TokenOutDTO.model_validate(token), "Token creation")
    except Exception as e:
        handle_error(e, "Token creation")

async def test_get_active_token(session, chat_session_id: int):
    print("\n=== Test: Get Active Token for Chat Session ===")
    try:
        async with session.begin():
            tokens = await token_service.get_active_token_by_chat(chat_session_id, session=session)
            token_dtos = [TokenOutDTO.model_validate(t) for t in tokens]
            check_response(token_dtos, "Get active token list")
            for token in token_dtos:
                print("-", token)
    except Exception as e:
        handle_error(e, "Get active token list")

# --- Abuse Tests ---

async def test_chat_session_with_invalid_user(session):
    print("\n=== Abuse Test: Chat Session with Invalid User ===")
    try:
        async with session.begin():
            dto = ChatSessionCreateDTO(
                litefarm_user_id=uuid4(),
                telegram_chat_id=int(uuid4().int % 1_000_000_000_000)
            )
            await chat_service.create_chat_session(dto, session=session)
    except IntegrityError as e:
        handle_error(e, "Create chat with invalid user")

async def test_token_for_invalid_chat_session(session):
    print("\n=== Abuse Test: Token for Invalid Chat Session ===")
    try:
        async with session.begin():
            dto = TokenCreateDTO(
                chat_session_id=9999999,
                token=str(uuid4()),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            await token_service.create_token(dto, session=session)
    except IntegrityError as e:
        handle_error(e, "Create token for invalid chat")

async def test_expired_token_not_returned(session):
    print("\n=== Abuse Test: Expired Token Not Returned ===")

    user_id = uuid4()
    telegram_chat_id = int(uuid4().int % 1_000_000_000_000)

    async with session.begin():
        user = await user_service.create_user(CreateUserDTO(litefarm_user_id=user_id), session=session)
        chat = await chat_service.create_chat_session(
            ChatSessionCreateDTO(litefarm_user_id=user_id, telegram_chat_id=telegram_chat_id),
            session=session
        )
        token = await token_service.create_token(
            TokenCreateDTO(
                chat_session_id=chat.id,
                token=str(uuid4()),
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)
            ),
            session=session
        )

    async with session.begin():
        tokens = await token_service.get_active_token_by_chat(chat.id, session=session)
        if tokens:
            print("❌ Expired token incorrectly returned")
        else:
            print("✅ Expired token correctly filtered out")

# --- Main ---

async def main():
    async with AsyncSessionLocal() as session:
        chat_session_id, telegram_chat_id = await test_create_chat_session_success(session)

        if chat_session_id is not None:
            await test_get_active_chat_session(session, telegram_chat_id=telegram_chat_id)
            await test_create_token_success(session, chat_session_id)
            await test_get_active_token(session, chat_session_id)
        else:
            print("❌ Skipping token tests: chat session creation failed")

        # Run abuse cases
        await test_chat_session_with_invalid_user(session)
        await test_token_for_invalid_chat_session(session)
        await test_expired_token_not_returned(session)

if __name__ == "__main__":
    asyncio.run(main())