from config import config
from aiogram.types import Message

## Login command that returns a link to the login page
async def cmd_login(message: Message):
    # Use chat.id instead of from_user.id for telegram_chat_id
    chat_id = message.chat.id
    login_text = (
        "Haz click en el siguiente link para iniciar sesión:\n"
        f'<a href="{config.LINK_SERVER}/login?chat_id={chat_id}">Iniciar sesión</a>\n\n'
        "<i>Nota: Copia y pega este enlace en tu navegador ya que no es HTTPS</i>\n"
        f"<code>{config.LINK_SERVER}/login?chat_id={chat_id}</code>"
    )
    await message.answer(login_text, parse_mode="HTML")
