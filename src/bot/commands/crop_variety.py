from aiogram.types import Message
from services.api import get_crop_varieties
from config import LOGIN_TOKEN

async def cmd_crop_varieties(message: Message):
    """
    Handles the /crop_varieties command to list available crop varieties for the user's farm.
    """
    if message.from_user is None:
        await message.answer("⚠️ No se pudo identificar al usuario. Por favor, intenta nuevamente.")
        return

    user_id = message.from_user.id

    # Burned values for now (replace with dynamic values later)
    farm_id = "5aa78ca8-3236-11f0-a33e-66ab45519382"  # Replace with dynamic farm_id
    token = LOGIN_TOKEN

    # Fetch the crop varieties
    result = await get_crop_varieties(farm_id, token)

    if result["success"]:
        crop_varieties = result["data"]
        if crop_varieties:
            response_text = "🌱 Variedades de cultivos disponibles:\n"
            for crop_variety in crop_varieties:
                # Use 'crop_variety_name' to display the name of the crop variety
                response_text += f"• {crop_variety['crop_variety_name']}\n"
            await message.answer(response_text)
        else:
            await message.answer("ℹ️ No se encontraron variedades de cultivos disponibles.")
    else:
        await message.answer(f"❌ Error al obtener las variedades de cultivos: {result['error']}")