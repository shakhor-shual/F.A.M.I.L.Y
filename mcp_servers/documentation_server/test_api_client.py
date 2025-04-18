#!/usr/bin/env python3
"""
Клиент для тестирования API сервера документации F.A.M.I.L.Y.

Этот скрипт позволяет удобно тестировать API сервера документации
без необходимости использования команд curl.
"""

import os
import json
import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api_client")

class DocumentationAPIClient:
    """
    Клиент для работы с API сервера документации F.A.M.I.L.Y.
    
    Предоставляет методы для взаимодействия с диаграммами документации
    через программный интерфейс вместо прямых вызовов curl.
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Инициализирует клиент API.
        
        Args:
            base_url: Базовый URL сервера документации (по умолчанию http://localhost:8080)
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
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверяет состояние сервера документации.
        
        Returns:
            Словарь с информацией о состоянии сервера
        """
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()
    
    async def get_all_diagrams(self, diagram_type: Optional[str] = None, 
                             query: Optional[str] = None) -> Dict[str, Any]:
        """
        Получает список всех диаграмм.
        
        Args:
            diagram_type: Фильтр по типу диаграммы (опционально)
            query: Поисковый запрос (опционально)
            
        Returns:
            Словарь со списком диаграмм
        """
        params = {}
        if diagram_type:
            params['type'] = diagram_type
        if query:
            params['query'] = query
        
        async with self.session.get(f"{self.base_url}/api/diagrams", params=params) as response:
            return await response.json()
    
    async def get_diagram(self, diagram_id: int) -> Dict[str, Any]:
        """
        Получает информацию о конкретной диаграмме по ID.
        
        Args:
            diagram_id: ID диаграммы
            
        Returns:
            Словарь с информацией о диаграмме
        """
        async with self.session.get(f"{self.base_url}/api/diagrams/{diagram_id}") as response:
            return await response.json()
    
    async def create_diagram(self, name: str, description: str, 
                           diagram_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает новую диаграмму.
        
        Args:
            name: Название диаграммы
            description: Описание диаграммы
            diagram_type: Тип диаграммы
            content: Содержимое диаграммы в формате JSON
            
        Returns:
            Словарь с результатом создания диаграммы
        """
        data = {
            'name': name,
            'description': description,
            'diagram_type': diagram_type,
            'content': content,
            'content_type': 'json'
        }
        
        async with self.session.post(f"{self.base_url}/api/diagrams", json=data) as response:
            return await response.json()
    
    async def update_diagram(self, diagram_id: int, name: Optional[str] = None,
                           description: Optional[str] = None, 
                           content: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Обновляет существующую диаграмму.
        
        Args:
            diagram_id: ID диаграммы для обновления
            name: Новое название диаграммы (опционально)
            description: Новое описание диаграммы (опционально)
            content: Новое содержимое диаграммы (опционально)
            
        Returns:
            Словарь с результатом обновления диаграммы
        """
        data = {}
        if name is not None:
            data['name'] = name
        if description is not None:
            data['description'] = description
        if content is not None:
            data['content'] = content
        
        async with self.session.put(f"{self.base_url}/api/diagrams/{diagram_id}", json=data) as response:
            return await response.json()
    
    async def delete_diagram(self, diagram_id: int) -> Dict[str, Any]:
        """
        Удаляет диаграмму по ID.
        
        Args:
            diagram_id: ID диаграммы для удаления
            
        Returns:
            Словарь с результатом удаления диаграммы
        """
        async with self.session.delete(f"{self.base_url}/api/diagrams/{diagram_id}") as response:
            return await response.json()
    
    async def verify_diagram(self, diagram_id: int, verified_by: str, 
                           status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Верифицирует диаграмму.
        
        Args:
            diagram_id: ID диаграммы для верификации
            verified_by: Имя верифицирующего (человек или АМИ)
            status: Статус верификации ('approved', 'rejected', 'needs_revision')
            notes: Заметки о верификации (опционально)
            
        Returns:
            Словарь с результатом верификации диаграммы
        """
        data = {
            'verified_by': verified_by,
            'status': status
        }
        
        if notes:
            data['notes'] = notes
        
        async with self.session.post(f"{self.base_url}/api/diagrams/{diagram_id}/verify", json=data) as response:
            return await response.json()

async def run_tests():
    """
    Запускает тесты всех функций API сервера документации.
    """
    async with DocumentationAPIClient() as client:
        print("\n=== Тестирование API сервера документации F.A.M.I.L.Y ===\n")
        
        # Проверка состояния сервера
        print("1. Проверка состояния сервера:")
        health = await client.health_check()
        print(json.dumps(health, indent=2, ensure_ascii=False))
        print("\n" + "="*60)
        
        # Получение списка всех диаграмм
        print("\n2. Получение списка всех диаграмм:")
        all_diagrams = await client.get_all_diagrams()
        print(json.dumps(all_diagrams, indent=2, ensure_ascii=False))
        print("\n" + "="*60)
        
        # Поиск диаграмм по типу
        print("\n3. Поиск диаграмм по типу 'architecture':")
        arch_diagrams = await client.get_all_diagrams(diagram_type="architecture")
        print(json.dumps(arch_diagrams, indent=2, ensure_ascii=False))
        print("\n" + "="*60)
        
        # Получение информации о конкретной диаграмме
        print("\n4. Получение информации о диаграмме с ID=2:")
        diagram = await client.get_diagram(2)
        print(json.dumps(diagram, indent=2, ensure_ascii=False))
        print("\n" + "="*60)
        
        # Создание новой диаграммы
        print("\n5. Создание новой диаграммы:")
        new_diagram_content = {
            "title": "Процесс верификации документации",
            "diagram_version": "1.0",
            "actors": [
                {
                    "id": "ami",
                    "name": "АМИ"
                },
                {
                    "id": "human",
                    "name": "Инженер"
                },
                {
                    "id": "system",
                    "name": "Система документации"
                }
            ],
            "sequence": [
                {
                    "from": "ami",
                    "to": "system",
                    "message": "Запрос на верификацию диаграммы"
                },
                {
                    "from": "system",
                    "to": "human",
                    "message": "Уведомление о запросе верификации"
                },
                {
                    "from": "human",
                    "to": "system",
                    "message": "Проверка и подтверждение"
                },
                {
                    "from": "system",
                    "to": "ami",
                    "message": "Уведомление о результате верификации"
                }
            ]
        }
        
        create_result = await client.create_diagram(
            name="Процесс верификации документации",
            description="Диаграмма последовательности процесса верификации документации в системе F.A.M.I.L.Y.",
            diagram_type="sequence",
            content=new_diagram_content
        )
        print(json.dumps(create_result, indent=2, ensure_ascii=False))
        print("\n" + "="*60)
        
        # Если создание диаграммы успешно, продолжаем с остальными тестами
        if create_result.get("success") and "diagram_id" in create_result:
            new_diagram_id = create_result["diagram_id"]
            
            # Обновление диаграммы
            print(f"\n6. Обновление диаграммы с ID={new_diagram_id}:")
            update_result = await client.update_diagram(
                diagram_id=new_diagram_id,
                description="Обновленное описание диаграммы процесса верификации документации."
            )
            print(json.dumps(update_result, indent=2, ensure_ascii=False))
            print("\n" + "="*60)
            
            # Верификация диаграммы
            print(f"\n7. Верификация диаграммы с ID={new_diagram_id}:")
            verify_result = await client.verify_diagram(
                diagram_id=new_diagram_id,
                verified_by="АМИ-инженер",
                status="approved",
                notes="Диаграмма корректно отображает процесс верификации."
            )
            print(json.dumps(verify_result, indent=2, ensure_ascii=False))
            print("\n" + "="*60)
            
            # Получение обновленной информации о диаграмме
            print(f"\n8. Получение информации об обновленной диаграмме с ID={new_diagram_id}:")
            updated_diagram = await client.get_diagram(new_diagram_id)
            print(json.dumps(updated_diagram, indent=2, ensure_ascii=False))
            print("\n" + "="*60)
            
            # Удаление диаграммы (закомментировано, чтобы сохранить диаграмму в системе)
            # print(f"\n9. Удаление диаграммы с ID={new_diagram_id}:")
            # delete_result = await client.delete_diagram(new_diagram_id)
            # print(json.dumps(delete_result, indent=2, ensure_ascii=False))
            # print("\n" + "="*60)
        else:
            print("Не удалось создать новую диаграмму, пропускаем остальные тесты.")
        
        print("\n=== Тестирование завершено ===\n")

if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except Exception as e:
        logger.error(f"Ошибка при выполнении тестов: {str(e)}")