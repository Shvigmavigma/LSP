# core/memory_store.py
import time
import re
from typing import Dict, Optional, Iterator

class MemoryStore:
    """Простое in-memory хранилище вместо Redis"""
    
    def __init__(self):
        self._store: Dict[str, dict] = {}
    
    def setex(self, key: str, seconds: int, value: str) -> None:
        """Сохранить значение с TTL"""
        self._store[key] = {
            'value': value,
            'expires_at': time.time() + seconds
        }
    
    def get(self, key: str) -> Optional[str]:
        """Получить значение, если не истекло"""
        data = self._store.get(key)
        if not data:
            return None
        
        if time.time() > data['expires_at']:
            del self._store[key]
            return None
        
        return data['value']
    
    def delete(self, key: str) -> None:
        """Удалить ключ"""
        if key in self._store:
            del self._store[key]
    
    def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        data = self._store.get(key)
        if not data:
            return False
        
        if time.time() > data['expires_at']:
            del self._store[key]
            return False
        
        return True
    
    def scan_iter(self, match: str = "*") -> Iterator[str]:
        """Имитация redis scan_iter для поиска ключей по паттерну"""
        pattern = match.replace('*', '.*').replace('?', '.')
        
        for key in list(self._store.keys()):
            if re.match(pattern, key):
                if self.exists(key):
                    yield key

# Создаём глобальный экземпляр
memory_store = MemoryStore()