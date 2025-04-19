"""
Простая реализация хранилища промптов для MCP сервера.
"""

from typing import Dict, Optional

class MemoryPromptStorage:
    """Хранилище промптов в памяти"""
    
    def __init__(self):
        self._storage: Dict[str, str] = {}
    
    def put(self, key: str, prompt: str) -> None:
        """Сохраняет промпт в хранилище"""
        self._storage[key] = prompt
    
    def get(self, key: str) -> Optional[str]:
        """Получает промпт из хранилища"""
        return self._storage.get(key)
    
    def delete(self, key: str) -> None:
        """Удаляет промпт из хранилища"""
        if key in self._storage:
            del self._storage[key]
    
    def list(self) -> Dict[str, str]:
        """Возвращает все промпты"""
        return self._storage.copy() 