#!/usr/bin/env python3
"""
MCP-клиент для взаимодействия АМИ с сервером документации F.A.M.I.L.Y.

Этот скрипт демонстрирует, как АМИ может самостоятельно взаимодействовать
с сервером документации через протокол MCP без участия человека.

Пример использования:
    python mcp_client.py get_diagrams
    python mcp_client.py get_diagram 2
    python mcp_client.py search_diagrams "память"
"""

import os
import sys
import json
import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional, List, Union
import argparse
from datetime import datetime
import uuid

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_client")

class AmiMcpClient:
    """
    MCP-клиент для самостоятельного взаимодействия АМИ с сервером документации F.A.M.I.L.Y.
    
    Демонстрирует, как АМИ может автономно обращаться к серверу документации
    для получения информации о многоуровневой модели памяти и других компонентах системы.
    
    Integration Points:
        - Взаимодействует с сервером документации через MCP
        - Позволяет АМИ обновлять и верифицировать документацию
        - Обеспечивает доступ к системным диаграммам из памяти АМИ
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Инициализирует MCP-клиент.
        
        Args:
            base_url: Базовый URL сервера документации
        """
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        """Создает сессию при входе в контекстный менеджер"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрывает сессию при выходе из контекстного менеджера"""
        if self.session:
            await self.session.close()
    
    async def _send_mcp_request(self, operation: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Отправляет MCP-запрос серверу документации.
        
        Args:
            operation: Название операции MCP
            params: Параметры операции
            
        Returns:
            Ответ сервера в формате словаря
        """
        if params is None:
            params = {}
        
        request_data = {
            "operation": operation,
            "params": params,
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"Отправка MCP-запроса: {json.dumps(request_data, ensure_ascii=False)}")
        
        async with self.session.post(f"{self.base_url}/mcp", json=request_data) as response:
            response_data = await response.json()
            logger.debug(f"Получен MCP-ответ: {json.dumps(response_data, ensure_ascii=False)}")
            
            return response_data
    
    async def get_diagrams(self) -> Dict[str, Any]:
        """
        Получает список всех диаграмм.
        
        Returns:
            Список диаграмм в формате словаря
        """
        return await self._send_mcp_request("get_diagrams")
    
    async def get_diagram(self, diagram_id: int) -> Dict[str, Any]:
        """
        Получает информацию о диаграмме по ID.
        
        Args:
            diagram_id: ID диаграммы
            
        Returns:
            Информация о диаграмме в формате словаря
        """
        return await self._send_mcp_request("get_diagram", {"diagram_id": diagram_id})
    
    async def create_diagram(self, name: str, description: str, 
                           diagram_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает новую диаграмму.
        
        Args:
            name: Название диаграммы
            description: Описание диаграммы
            diagram_type: Тип диаграммы
            content: Содержимое диаграммы
            
        Returns:
            Результат создания диаграммы в формате словаря
        """
        params = {
            "name": name,
            "description": description,
            "diagram_type": diagram_type,
            "content": content
        }
        
        return await self._send_mcp_request("create_diagram", params)
    
    async def update_diagram(self, diagram_id: int, name: Optional[str] = None,
                           description: Optional[str] = None, 
                           content: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Обновляет существующую диаграмму.
        
        Args:
            diagram_id: ID диаграммы
            name: Новое название диаграммы (опционально)
            description: Новое описание диаграммы (опционально)
            content: Новое содержимое диаграммы (опционально)
            
        Returns:
            Результат обновления диаграммы в формате словаря
        """
        params = {"diagram_id": diagram_id}
        
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
        if content is not None:
            params["content"] = content
            
        return await self._send_mcp_request("update_diagram", params)
    
    async def verify_diagram(self, diagram_id: int, verified_by: str, 
                           status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Верифицирует диаграмму.
        
        Args:
            diagram_id: ID диаграммы
            verified_by: Имя верифицирующего
            status: Статус верификации ('approved', 'rejected', 'needs_revision')
            notes: Заметки о верификации (опционально)
            
        Returns:
            Результат верификации диаграммы в формате словаря
        """
        params = {
            "diagram_id": diagram_id,
            "verified_by": verified_by,
            "status": status
        }
        
        if notes is not None:
            params["notes"] = notes
            
        return await self._send_mcp_request("verify_diagram", params)
    
    async def search_diagrams(self, query: str) -> Dict[str, Any]:
        """
        Выполняет поиск диаграмм по запросу.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных диаграмм в формате словаря
        """
        return await self._send_mcp_request("search_diagrams", {"query": query})
    
    async def get_diagrams_by_type(self, diagram_type: str) -> Dict[str, Any]:
        """
        Получает список диаграмм определенного типа.
        
        Args:
            diagram_type: Тип диаграмм для поиска
            
        Returns:
            Список диаграмм указанного типа в формате словаря
        """
        return await self._send_mcp_request("get_diagrams_by_type", {"diagram_type": diagram_type})

async def main():
    """
    Основная функция для работы с MCP-клиентом из командной строки.
    """
    parser = argparse.ArgumentParser(description="MCP-клиент для сервера документации F.A.M.I.L.Y.")
    parser.add_argument("operation", choices=[
        "get_diagrams", "get_diagram", "search_diagrams", 
        "get_diagrams_by_type", "create_diagram", "update_diagram",
        "verify_diagram"
    ], help="Операция MCP для выполнения")
    parser.add_argument("args", nargs="*", help="Аргументы операции")
    parser.add_argument("--server", default="http://localhost:8080", help="URL сервера документации")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    
    args = parser.parse_args()
    
    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger("mcp_client").setLevel(logging.DEBUG)
    
    try:
        async with AmiMcpClient(args.server) as client:
            # Вызываем соответствующую операцию
            if args.operation == "get_diagrams":
                response = await client.get_diagrams()
                print_response(response)
                
            elif args.operation == "get_diagram":
                if not args.args:
                    print("Ошибка: Не указан ID диаграммы")
                    sys.exit(1)
                    
                diagram_id = int(args.args[0])
                response = await client.get_diagram(diagram_id)
                print_response(response)
                
            elif args.operation == "search_diagrams":
                if not args.args:
                    print("Ошибка: Не указан поисковый запрос")
                    sys.exit(1)
                    
                query = args.args[0]
                response = await client.search_diagrams(query)
                print_response(response)
                
            elif args.operation == "get_diagrams_by_type":
                if not args.args:
                    print("Ошибка: Не указан тип диаграмм")
                    sys.exit(1)
                    
                diagram_type = args.args[0]
                response = await client.get_diagrams_by_type(diagram_type)
                print_response(response)
                
            elif args.operation == "create_diagram":
                print("Создание новой диаграммы из файла не поддерживается в этой версии cli")
                print("Используйте программный интерфейс AmiMcpClient для этой операции")
                
            elif args.operation == "update_diagram":
                print("Обновление диаграммы из файла не поддерживается в этой версии cli")
                print("Используйте программный интерфейс AmiMcpClient для этой операции")
                
            elif args.operation == "verify_diagram":
                if len(args.args) < 3:
                    print("Ошибка: Не хватает аргументов. Формат: verify_diagram <id> <verified_by> <status> [notes]")
                    sys.exit(1)
                    
                diagram_id = int(args.args[0])
                verified_by = args.args[1]
                status = args.args[2]
                notes = args.args[3] if len(args.args) > 3 else None
                
                response = await client.verify_diagram(diagram_id, verified_by, status, notes)
                print_response(response)
            
    except ValueError as e:
        print(f"Ошибка: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        sys.exit(1)

def print_response(response: Dict[str, Any]):
    """
    Выводит ответ сервера в удобочитаемом формате.
    
    Args:
        response: Ответ сервера
    """
    print(json.dumps(response, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())