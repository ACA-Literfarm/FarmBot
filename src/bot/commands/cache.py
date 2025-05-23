from aiogram.types import Message
from cache import crop_cache
import json
import logging

async def cmd_cache_info(message: Message):
    """
    Shows cache information for debugging purposes.
    """
    logging.info("Cache info requested")
    cache_info = crop_cache.get_cache_info()
    
    response = f"📊 **Información del Caché de Cultivos**\n\n"
    response += f"Entradas totales: {cache_info['total_entries']}\n\n"
    
    if cache_info['entries']:
        for entry in cache_info['entries']:
            status = "❌ Expirado" if entry['is_expired'] else "✅ Válido"
            response += f"🔑 {entry['key'][:20]}...\n"
            response += f"   {status} | {entry['age_minutes']:.1f}min | {entry['data_count']} variedades\n\n"
    else:
        response += "🔍 No hay entradas en caché\n"
    
    await message.answer(response)

async def cmd_clear_cache(message: Message):
    """
    Clears the crop variety cache.
    """
    crop_cache.clear_cache()
    await message.answer("🗑️ Caché de variedades de cultivos limpiado exitosamente.")