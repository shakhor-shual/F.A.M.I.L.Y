#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Client для тестирования сервера документации F.A.M.I.L.Y.

Этот модуль реализует клиент для тестирования MCP-сервера, используя официальный пакет mcp.
"""

import asyncio
import logging
from typing import Dict, Any
from mcp.client import MCPClient
from mcp.client.context import Context

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentationClient:
    """
    Клиент для взаимодействия с MCP-сервером документации.
    
    Обеспечивает:
    - Установку соединения с сервером
    - Отправку и получение сообщений
    - Обработку ошибок
    - Аутентификацию
    - Управление сессией
    """
    
    def __init__(self, url: str = "http://localhost:8080"):
        """
        Инициализирует MCP-клиент.
        
        Args:
            url: URL сервера
        """
        self.url = url
        self.client = MCPClient(url)
    
    async def connect(self) -> None:
        """
        Устанавливает соединение с сервером.
        """
        try:
            await self.client.connect()
            logger.info(f"Connected to MCP server at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """
        Закрывает соединение с сервером.
        """
        await self.client.disconnect()
        logger.info("Disconnected from MCP server")
    
    async def get_diagrams(self) -> Dict[str, Any]:
        """
        Запрашивает список диаграмм.
        
        Returns:
            Список диаграмм
        """
        try:
            return await self.client.call("get_diagrams")
        except Exception as e:
            logger.error(f"Error getting diagrams: {e}")
            raise
    
    async def get_documentation(self, path: str) -> Dict[str, Any]:
        """
        Запрашивает документацию по указанному пути.
        
        Args:
            path: Путь к документации
            
        Returns:
            Содержимое документации
        """
        try:
            return await self.client.call("get_documentation", path=path)
        except Exception as e:
            logger.error(f"Error getting documentation: {e}")
            raise
    
    async def get_server_config(self) -> Dict[str, Any]:
        """
        Запрашивает конфигурацию сервера.
        
        Returns:
            Конфигурация сервера
        """
        try:
            return await self.client.get_resource("config://server")
        except Exception as e:
            logger.error(f"Error getting server config: {e}")
            raise

async def test_client():
    """Тестирует клиент"""
    client = DocumentationClient()
    try:
        await client.connect()
        
        # Получаем конфигурацию сервера
        config = await client.get_server_config()
        logger.info(f"Server config: {config}")
        
        # Получаем список диаграмм
        diagrams = await client.get_diagrams()
        logger.info(f"Diagrams: {diagrams}")
        
        # Получаем документацию
        doc = await client.get_documentation("test")
        logger.info(f"Documentation: {doc}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_client())