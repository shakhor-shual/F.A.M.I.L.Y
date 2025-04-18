#!/usr/bin/env python3
"""
Скрипт для проверки интеграции MCP-сервера документации F.A.M.I.L.Y. с VS Code.

Этот скрипт проверяет доступность MCP-сервера и имитирует запросы,
которые могут поступать от VS Code Copilot.

Пример использования:
    python test_mcp_integration.py
"""

import os
import sys
import json
import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional
import argparse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_integration_test")

# MCP-конфигурация
MCP_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "vscode_mcp_config.json")
MCP_SERVER_URL = "http://localhost:8080/mcp"  # Исправлен адрес на базовый MCP-эндпойнт

class McpIntegrationTester:
    """
    Тестировщик MCP-интеграции для проекта F.A.M.I.L.Y.
    
    Проверяет доступность MCP-сервера документации и 
    корректность обработки MCP-запросов.
    """
    
    def __init__(self, server_url: str = MCP_SERVER_URL):
        """
        Инициализирует тестировщик MCP-интеграции.
        
        Args:
            server_url: URL MCP-сервера документации
        """
        self.server_url = server_url
        self.session = None
    
    async def __aenter__(self):
        """Создает сессию при входе в контекстный менеджер"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрывает сессию при выходе из контекстного менеджера"""
        if self.session:
            await self.session.close()
    
    async def send_mcp_request(self, operation: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        
        # Формируем MCP-запрос
        request_data = {
            "operation": operation,
            "params": params
        }
        
        logger.info(f"Отправка MCP-запроса: {json.dumps(request_data, ensure_ascii=False)}")
        
        try:
            async with self.session.post(self.server_url, json=request_data) as response:
                if response.status != 200:
                    logger.error(f"Сервер вернул ошибку HTTP: {response.status}")
                    return {"status": "error", "error": {"message": f"Ошибка HTTP: {response.status}"}}
                
                try:
                    response_data = await response.json()
                    logger.info(f"Получен MCP-ответ со статусом {response.status}")
                    return response_data
                except Exception as e:
                    logger.error(f"Ошибка при парсинге JSON-ответа: {str(e)}")
                    response_text = await response.text()
                    logger.error(f"Ответ сервера: {response_text[:500]}...")
                    return {"status": "error", "error": {"message": f"Ошибка парсинга JSON: {str(e)}"}}
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при отправке MCP-запроса: {str(e)}")
            return {"status": "error", "error": {"message": f"Ошибка соединения: {str(e)}"}}
    
    async def test_server_availability(self) -> bool:
        """
        Проверяет доступность MCP-сервера через пинг-запрос.
        
        Returns:
            True, если сервер доступен, иначе False
        """
        try:
            # Отправляем простой запрос на получение списка диаграмм для проверки доступности сервера
            response = await self.send_mcp_request("ping", {"message": "test"})
            
            if response.get("status") == "success" or "diagrams" in response.get("data", {}):
                logger.info("MCP-сервер документации доступен и отвечает на запросы")
                return True
            else:
                # Если ping не работает, пробуем получить список диаграмм
                response = await self.send_mcp_request("get_diagrams")
                if response.get("status") == "success" or "diagrams" in response.get("data", {}):
                    logger.info("MCP-сервер документации доступен и отвечает на запросы")
                    return True
                else:
                    logger.error(f"MCP-сервер недоступен или вернул ошибку: {json.dumps(response, ensure_ascii=False)}")
                    return False
        except Exception as e:
            logger.error(f"Ошибка при проверке доступности MCP-сервера: {str(e)}")
            return False
    
    async def test_get_diagrams(self) -> bool:
        """
        Тестирует получение списка диаграмм через MCP.
        
        Returns:
            True, если тест прошел успешно, иначе False
        """
        response = await self.send_mcp_request("get_diagrams")
        
        if response.get("status") == "success":
            diagrams = response.get("data", {}).get("diagrams", [])
            logger.info(f"Получен список диаграмм через MCP. Количество: {len(diagrams)}")
            
            # Выводим краткую информацию о первых 3 диаграммах
            for i, diagram in enumerate(diagrams[:3]):
                logger.info(f"Диаграмма {i+1}: {diagram.get('name')} (ID: {diagram.get('id')})")
                
            return True
        else:
            error_msg = response.get("error", {}).get("message", "Неизвестная ошибка")
            logger.error(f"Ошибка при получении списка диаграмм: {error_msg}")
            return False
    
    async def test_get_diagram_by_id(self, diagram_id: int = 2) -> bool:
        """
        Тестирует получение диаграммы по ID через MCP.
        
        Args:
            diagram_id: ID диаграммы для получения
            
        Returns:
            True, если тест прошел успешно, иначе False
        """
        response = await self.send_mcp_request("get_diagram", {"diagram_id": diagram_id})
        
        if response.get("status") == "success":
            diagram = response.get("data", {}).get("diagram", {})
            logger.info(f"Получена диаграмма через MCP: {diagram.get('name')} (ID: {diagram.get('id')})")
            logger.info(f"Описание: {diagram.get('description')}")
            return True
        else:
            error_msg = response.get("error", {}).get("message", "Неизвестная ошибка")
            logger.error(f"Ошибка при получении диаграммы по ID: {error_msg}")
            return False
    
    async def test_vs_code_integration(self) -> None:
        """
        Имитирует запросы, которые могут поступать от VS Code через MCP.
        
        Этот метод проверяет сценарий использования MCP-сервера из VS Code,
        отправляя запросы в формате, ожидаемом от VS Code Copilot.
        """
        # Выводим конфигурацию MCP
        try:
            with open(MCP_CONFIG_PATH, 'r') as config_file:
                config = json.load(config_file)
                action_count = len(config.get('actions', []))
                logger.info(f"Загружена MCP-конфигурация: {action_count} операций")
                
                # Проверяем доступные операции
                for action in config.get('actions', []):
                    logger.info(f"Доступная MCP-операция: {action.get('name')} - {action.get('description')}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке MCP-конфигурации: {str(e)}")
            return
        
        # Имитируем запрос от VS Code на получение списка диаграмм
        logger.info("\n=== Имитация запроса от VS Code: получение списка диаграмм ===")
        await self.test_get_diagrams()
        
        # Имитируем запрос от VS Code на получение конкретной диаграммы
        logger.info("\n=== Имитация запроса от VS Code: получение диаграммы по ID ===")
        await self.test_get_diagram_by_id(2)

async def main():
    """
    Основная функция для запуска тестирования MCP-интеграции.
    """
    parser = argparse.ArgumentParser(description="Тестирование MCP-интеграции для F.A.M.I.L.Y.")
    parser.add_argument("--url", default=MCP_SERVER_URL, help="URL MCP-сервера")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    
    args = parser.parse_args()
    
    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger("mcp_integration_test").setLevel(logging.DEBUG)
    
    print("\n")
    logger.info("=" * 80)
    logger.info("Тестирование MCP-интеграции для F.A.M.I.L.Y.")
    logger.info("=" * 80)
    
    try:
        async with McpIntegrationTester(args.url) as tester:
            # Проверяем доступность сервера
            logger.info("\nПроверка доступности MCP-сервера документации...")
            if await tester.test_server_availability():
                logger.info("✓ MCP-сервер документации доступен.")
                
                # Тестируем интеграцию с VS Code
                logger.info("\nТестирование интеграции с VS Code...")
                await tester.test_vs_code_integration()
                
                logger.info("\n✓ Тестирование MCP-интеграции завершено.")
            else:
                logger.error("✗ MCP-сервер документации недоступен. Убедитесь, что он запущен.")
    except Exception as e:
        logger.error(f"Ошибка при тестировании MCP-интеграции: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())