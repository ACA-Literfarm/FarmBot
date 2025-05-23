import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from services.api import get_crop_varieties
from config import FARM_ID, LOGIN_TOKEN

class CropVarietyCache:
    def __init__(self, cache_duration_minutes: int = 30):
        """
        Initialize the crop variety cache.
        
        Args:
            cache_duration_minutes: How long to cache crop varieties (default: 30 minutes)
        """
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get_crop_varieties(self, farm_id: str, token: str) -> Dict[str, Any]:
        """
        Get crop varieties from cache or fetch from API if cache is expired/empty.
        
        Args:
            farm_id: The farm ID
            token: Authorization token
            
        Returns:
            Dict containing success status and crop varieties data
        """
        async with self._lock:
            cache_key = f"{farm_id}:{token[:10]}"  # Use farm_id and part of token as key
            current_time = datetime.now()
            
            # Check if we have valid cached data
            if cache_key in self._cache:
                cached_data = self._cache[cache_key]
                if current_time - cached_data["timestamp"] < self.cache_duration:
                    logging.info(f"Using cached crop varieties for farm {farm_id}")
                    return {
                        "success": True,
                        "data": cached_data["data"],
                        "from_cache": True
                    }
                else:
                    logging.info(f"Cache expired for farm {farm_id}, fetching new data")
            
            # Cache miss or expired - fetch from API
            logging.info(f"Fetching crop varieties from API for farm {farm_id}")
            result = await get_crop_varieties(farm_id, token)
            
            if result["success"]:
                # Cache the successful result
                self._cache[cache_key] = {
                    "data": result["data"],
                    "timestamp": current_time
                }
                logging.info(f"Cached crop varieties for farm {farm_id}")
                result["from_cache"] = False
            
            return result
    
    def clear_cache(self, farm_id: Optional[str] = None):
        """
        Clear cache for a specific farm or all farms.
        
        Args:
            farm_id: Specific farm to clear cache for, or None to clear all
        """
        if farm_id:
            # Clear cache for specific farm
            keys_to_remove = [key for key in self._cache.keys() if key.startswith(f"{farm_id}:")]
            for key in keys_to_remove:
                del self._cache[key]
            logging.info(f"Cleared cache for farm {farm_id}")
        else:
            # Clear all cache
            self._cache.clear()
            logging.info("Cleared all crop variety cache")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the current cache state.
        
        Returns:
            Dict with cache statistics
        """
        current_time = datetime.now()
        cache_info = {
            "total_entries": len(self._cache),
            "entries": []
        }
        
        for key, data in self._cache.items():
            age = current_time - data["timestamp"]
            cache_info["entries"].append({
                "key": key,
                "age_minutes": age.total_seconds() / 60,
                "is_expired": age > self.cache_duration,
                "data_count": len(data["data"])
            })
        
        return cache_info

# Global cache instance
crop_cache = CropVarietyCache(cache_duration_minutes=30)