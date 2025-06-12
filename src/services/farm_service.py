"""
Farm management service for handling farm selection and storage.
"""
import json
import os
from typing import Optional, Dict, Any, List
import logging
from .api_service import request_user_farms

class FarmService:
    """Service to manage farm selection and storage."""
    
    def __init__(self):
        self.user_farms_file = "cache/user_farms.json"
        self.selected_farms_file = "cache/selected_farms.json"
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        os.makedirs("cache", exist_ok=True)
    
    async def get_user_farms(self, user_id: str, force_refresh: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        Get farms for a user, either from cache or API.
        
        Args:
            user_id: Telegram user ID
            force_refresh: Force refresh from API
            
        Returns:
            List of farms or None if error
        """
        if not force_refresh:
            cached_farms = self._get_cached_farms(user_id)
            if cached_farms:
                return cached_farms
        
        # Fetch from API
        farms = await request_user_farms()
        if farms:
            self._cache_user_farms(user_id, farms)
            return farms
        
        return None
    
    def _get_cached_farms(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached farms for user."""
        try:
            if os.path.exists(self.user_farms_file):
                with open(self.user_farms_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get(user_id, [])
        except Exception as e:
            logging.error(f"Error reading cached farms: {e}")
        return None
    
    def _cache_user_farms(self, user_id: str, farms: List[Dict[str, Any]]):
        """Cache user farms."""
        try:
            data = {}
            if os.path.exists(self.user_farms_file):
                with open(self.user_farms_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data[user_id] = farms
            
            with open(self.user_farms_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"Error caching farms: {e}")
    
    def set_selected_farm(self, user_id: str, farm_id: str, farm_name: str) -> bool:
        """
        Set selected farm for user.
        
        Args:
            user_id: Telegram user ID
            farm_id: Selected farm ID
            farm_name: Selected farm name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {}
            if os.path.exists(self.selected_farms_file):
                with open(self.selected_farms_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data[user_id] = {
                "farm_id": farm_id,
                "farm_name": farm_name
            }
            
            with open(self.selected_farms_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logging.error(f"Error setting selected farm: {e}")
            return False
    
    def get_selected_farm(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        Get selected farm for user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dict with farm_id and farm_name, or None if no farm selected
        """
        try:
            if os.path.exists(self.selected_farms_file):
                with open(self.selected_farms_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get(user_id)
        except Exception as e:
            logging.error(f"Error getting selected farm: {e}")
        return None
    
    def remove_selected_farm(self, user_id: str) -> bool:
        """
        Remove farm selection for user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.selected_farms_file):
                with open(self.selected_farms_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if user_id in data:
                    del data[user_id]
                    
                    with open(self.selected_farms_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logging.error(f"Error removing selected farm: {e}")
            return False

# Global farm service instance
farm_service = FarmService()