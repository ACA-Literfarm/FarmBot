"""
Farm selection command for FarmBot.
"""
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import logging
from services.farm_service import farm_service

async def cmd_select_farm(message: Message) -> None:
    """
    Handle /selectfarm command to show available farms.
    """
    user_id = str(message.from_user.id)
    
    try:
        # Get user farms
        farms = await farm_service.get_user_farms(user_id, force_refresh=True)
        
        if not farms:
            await message.answer(
                "❌ No tienes granjas asociadas a tu cuenta.\n\n"
                "Para usar FarmBot, necesitas crear una granja primero. "
                "Ve a la aplicación web de LiteFarm para crear tu granja y luego regresa aquí. 🌱"
            )
            return
        
        # Create inline keyboard with farm options
        keyboard = []
        for farm in farms:
            farm_id = farm.get('farm_id', '')
            farm_name = farm.get('farm_name', 'Sin nombre')
            
            keyboard.append([
                InlineKeyboardButton(
                    text=f"🏡 {farm_name}", 
                    callback_data=f"select_farm:{farm_id}:{farm_name}"
                )
            ])
        
        # Add option to remove selection
        keyboard.append([
            InlineKeyboardButton(text="❌ Quitar selección", callback_data="remove_farm_selection")
        ])
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        # Show current selection if any
        current_farm = farm_service.get_selected_farm(user_id)
        current_info = ""
        if current_farm:
            current_info = f"\n\n🟢 Granja actual: **{current_farm['farm_name']}**"
        
        await message.answer(
            f"🏡 **Selecciona tu granja**\n\n"
            f"Elige la granja con la que quieres trabajar:{current_info}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logging.error(f"Error in cmd_select_farm: {e}")
        await message.answer(
            "❌ Ocurrió un error al obtener tus granjas. "
            "Por favor, inténtalo de nuevo en unos momentos."
        )

async def handle_farm_selection_callback(callback_query: CallbackQuery) -> None:
    """
    Handle farm selection from inline keyboard.
    """
    user_id = str(callback_query.from_user.id)
    
    try:
        await callback_query.answer()
        
        if callback_query.data == "remove_farm_selection":
            # Remove farm selection
            success = farm_service.remove_selected_farm(user_id)
            if success:
                await callback_query.message.edit_text(
                    "✅ Has quitado la selección de granja.\n\n"
                    "Puedes usar /selectfarm cuando quieras elegir una granja nuevamente."
                )
            else:
                await callback_query.message.edit_text("❌ Error al quitar la selección de granja.")
            return
        
        # Parse farm selection
        if callback_query.data.startswith("select_farm:"):
            parts = callback_query.data.split(":", 2)
            if len(parts) >= 3:
                farm_id = parts[1]
                farm_name = parts[2]
                
                # Validate farm exists in user's farms
                farms = await farm_service.get_user_farms(user_id)
                if farms and any(f.get('farm_id') == farm_id for f in farms):
                    # Set selected farm
                    success = farm_service.set_selected_farm(user_id, farm_id, farm_name)
                    if success:
                        await callback_query.message.edit_text(
                            f"✅ **Granja seleccionada:** {farm_name}\n\n"
                            f"Ahora puedes registrar transacciones para esta granja. "
                            f"Usa /selectfarm si quieres cambiar de granja. 🌱",
                            parse_mode='Markdown'
                        )
                    else:
                        await callback_query.message.edit_text("❌ Error al seleccionar la granja.")
                else:
                    await callback_query.message.edit_text(
                        "❌ Granja no válida. Por favor, usa /selectfarm para ver las opciones disponibles."
                    )
            else:
                await callback_query.message.edit_text("❌ Selección inválida.")
        
    except Exception as e:
        logging.error(f"Error in handle_farm_selection_callback: {e}")
        await callback_query.message.edit_text(
            "❌ Ocurrió un error al procesar tu selección. "
            "Por favor, inténtalo de nuevo."
        )