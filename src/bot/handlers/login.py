from aiogram.types import Message
from bot.state import user_states
from services.login import login_user

async def handle_login_flow(message: Message):
    """
    Handles the login flow by asking for username and password.
    """
    if message.from_user is None:
        await message.answer("⚠️ No se pudo identificar al usuario. Por favor, intenta nuevamente.")
        return
    user_id = message.from_user.id
    if user_id not in user_states:
        await message.answer("⚠️ No se inició el proceso de inicio de sesión. Usa /login para comenzar.")
        return

    state = user_states[user_id]

    # Step 1: Ask for the username
    if state["state"] == "awaiting_username":
        state["username"] = message.text.strip() if message.text else ""
        state["state"] = "awaiting_password"
        await message.answer("🔒 Por favor, ingresa tu contraseña:")
        return

    # Step 2: Ask for the password
    if state["state"] == "awaiting_password":
        state["password"] = message.text.strip() if message.text else ""
        username = state["username"]
        password = state["password"]

        # Call the login API
        result = await login_user(username, password)

        if "error" in result:
            await message.answer(f"❌ Error al iniciar sesión: {result['error']}")
        else:
            token = result["token"]
            user_id = result["user_id"]
            farm_id = result["farm_id"]
            await message.answer(
                f"✅ Inicio de sesión exitoso:\n"
                f"🔑 Token: {token}\n"
                f"👤 User ID: {user_id}\n"
                f"🌾 Farm ID: {farm_id}"
            )

        # Clear the user's state
        del user_states[user_id]
        return