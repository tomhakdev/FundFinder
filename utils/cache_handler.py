import json
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class CacheHandler:
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self.ensure_cache_dir_exists()
        
    def ensure_cache_dir_exists(self):
        """Create cache directory if it doesn't exist"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
    def get_cache_path(self, symbol: str) -> str:
        """Get the cache file path for a symbol"""
        return os.path.join(self.cache_dir, f"{symbol.lower()}_cache.json")
        
    def get_cached_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached data if it exists and is not expired"""
        cache_path = self.get_cache_path(symbol)
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                    
                # Check if cache is expired (24 hours)
                cache_time = datetime.fromtimestamp(cached_data['cache_timestamp'])
                if datetime.now() - cache_time < timedelta(hours=24):
                    return cached_data['data']
            except Exception as e:
                print(f"Error reading cache for {symbol}: {str(e)}")
        
        return None
        
    def save_to_cache(self, symbol: str, data: Dict[str, Any]):
        """Save data to cache with timestamp"""
        cache_path = self.get_cache_path(symbol)
        
        try:
            cache_data = {
                'data': data,
                'cache_timestamp': datetime.now().timestamp()
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Error saving cache for {symbol}: {str(e)}")