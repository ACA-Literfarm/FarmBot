from aiogram.types import Message
from services.api import get_revenue_types
from config import LOGIN_TOKEN

async def cmd_revenue_types(message: Message):
    """
    Handles the /revenue_types command to list available revenue types for the user's farm.
    """
    if message.from_user is None:
        await message.answer("⚠️ No se pudo identificar al usuario. Por favor, intenta nuevamente.")
        return

    user_id = message.from_user.id

    # Burned values for now (replace with dynamic values later)
    farm_id = "5aa78ca8-3236-11f0-a33e-66ab45519382"  # Replace with dynamic farm_id
    token = LOGIN_TOKEN

    # Fetch the revenue types
    result = await get_revenue_types(farm_id, token)

    if result["success"]:
        revenue_types = result["data"]
        if revenue_types:
            response_text = "📋 Tipos de ingresos disponibles:\n"
            for revenue_type in revenue_types:
                response_text += f"• {revenue_type['revenue_name']}\n"
            await message.answer(response_text)
        else:
            await message.answer("ℹ️ No se encontraron tipos de ingresos disponibles.")
    else:
        await message.answer(f"❌ Error al obtener los tipos de ingresos: {result['error']}")