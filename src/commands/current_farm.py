"""
Current farm status command for FarmBot.
"""
from aiogram.types import Message
import logging
from services.farm_service import farm_service

async def cmd_current_farm(message: Message) -> None:
    """
    Handle /currentfarm command to show currently selected farm.
    """
    user_id = str(message.from_user.id)
    
    try:
        current_farm = farm_service.get_selected_farm(user_id)
        
        if current_farm:
            await message.answer(
                f"🟢 **Granja actual:** {current_farm['farm_name']}\n\n"
                f"Todas las transacciones se registrarán en esta granja.\n"
                f"Usa /selectfarm para cambiar de granja.",
                parse_mode='Markdown'
            )
        else:
            await message.answer(
                "❌ No tienes ninguna granja seleccionada.\n\n"
                "Usa /selectfarm para elegir una granja antes de registrar transacciones."
            )
            
    except Exception as e:
        logging.error(f"Error in cmd_current_farm: {e}")
        await message.answer(
            "❌ Ocurrió un error al obtener la información de tu granja actual."
        )