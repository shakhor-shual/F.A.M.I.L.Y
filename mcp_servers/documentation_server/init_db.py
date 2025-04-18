#!/usr/bin/env python3
"""
Initialization script for F.A.M.I.L.Y. Documentation Server database.

Этот скрипт создаёт необходимые структуры базы данных для сервера документации
и добавляет начальные данные для работы с диаграммами.

Integration Points:
    - Использует параметры подключения из модуля db.connection
    - Создаёт схемы и таблицы для хранения документации
"""

import asyncio
import logging
import json
import os
import sys

# Добавляем текущую директорию в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from documentation_server.db.connection import setup_database, db_transaction, close_db_pool
from documentation_server.models.diagram import DiagramModel

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_database():
    """
    Инициализирует структуру базы данных и добавляет начальные данные.
    """
    try:
        logger.info("Начало инициализации базы данных...")
        
        # Создание схем и таблиц
        await setup_database()
        logger.info("Структура базы данных успешно создана")
        
        # Добавление тестовых диаграмм
        await create_test_diagrams()
        logger.info("Тестовые диаграммы успешно добавлены")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {str(e)}")
        raise
    finally:
        # Закрываем пул соединений
        await close_db_pool()

async def create_test_diagrams():
    """
    Создает тестовые диаграммы в базе данных.
    """
    # Проверяем, есть ли уже диаграммы в базе
    async with db_transaction() as conn:
        count = await conn.fetchval("""
            SELECT COUNT(id) FROM ami_documentation.diagrams
        """)
        
        if count > 0:
            logger.info(f"В базе уже есть {count} диаграмм, пропускаем добавление тестовых данных")
            return
    
    logger.info("Добавление тестовых диаграмм...")
    
    # Создаем архитектурную диаграмму системы памяти
    memory_system_diagram = {
        "title": "Многоуровневая модель памяти АМИ",
        "diagram_version": "1.0",
        "nodes": [
            {
                "id": "consciousness",
                "type": "memory_level",
                "name": "Уровень сознания",
                "description": "Явные воспоминания и опыт"
            },
            {
                "id": "subconsciousness",
                "type": "memory_level",
                "name": "Уровень подсознания",
                "description": "Скрытые связи и ассоциации"
            },
            {
                "id": "deepmind",
                "type": "memory_level",
                "name": "Глубинный уровень",
                "description": "Базовые принципы и абстрактные знания"
            }
        ],
        "edges": [
            {
                "source": "consciousness",
                "target": "subconsciousness",
                "type": "interaction",
                "name": "Погружение"
            },
            {
                "source": "subconsciousness",
                "target": "deepmind",
                "type": "interaction",
                "name": "Абстрагирование"
            },
            {
                "source": "deepmind",
                "target": "consciousness",
                "type": "interaction",
                "name": "Проявление"
            }
        ]
    }
    
    await DiagramModel.create_diagram(
        name="Модель многоуровневой памяти",
        description="Архитектурная диаграмма многоуровневой модели памяти АМИ",
        diagram_type="architecture",
        content=memory_system_diagram,
        is_json=True
    )
    
    # Создаем компонентную диаграмму сознательного уровня
    consciousness_components = {
        "title": "Компоненты сознательного уровня",
        "diagram_version": "1.0",
        "components": [
            {
                "id": "experience_service",
                "type": "service",
                "name": "Сервис опыта",
                "description": "Обрабатывает и хранит явный опыт АМИ"
            },
            {
                "id": "session_manager",
                "type": "manager",
                "name": "Менеджер сессий",
                "description": "Управляет активными сессиями взаимодействия"
            },
            {
                "id": "memory_storage",
                "type": "storage",
                "name": "Хранилище воспоминаний",
                "description": "Персистентное хранилище для воспоминаний"
            }
        ],
        "connections": [
            {
                "source": "experience_service",
                "target": "session_manager",
                "type": "uses"
            },
            {
                "source": "experience_service",
                "target": "memory_storage",
                "type": "reads_writes"
            },
            {
                "source": "session_manager",
                "target": "memory_storage",
                "type": "reads"
            }
        ]
    }
    
    await DiagramModel.create_diagram(
        name="Компоненты сознательного уровня",
        description="Диаграмма компонентов сознательного уровня памяти АМИ",
        diagram_type="component",
        content=consciousness_components,
        is_json=True
    )
    
    # Создаем диаграмму последовательности для процесса запоминания
    memory_sequence = {
        "title": "Процесс запоминания опыта",
        "diagram_version": "1.0",
        "actors": [
            {
                "id": "human",
                "name": "Человек"
            },
            {
                "id": "ami",
                "name": "АМИ"
            },
            {
                "id": "memory_system",
                "name": "Система памяти"
            }
        ],
        "sequence": [
            {
                "from": "human",
                "to": "ami",
                "message": "Взаимодействие с АМИ"
            },
            {
                "from": "ami",
                "to": "memory_system",
                "message": "Фиксация опыта"
            },
            {
                "from": "memory_system",
                "to": "memory_system",
                "message": "Обработка и классификация"
            },
            {
                "from": "memory_system",
                "to": "ami",
                "message": "Подтверждение сохранения"
            },
            {
                "from": "ami",
                "to": "human",
                "message": "Обратная связь"
            }
        ]
    }
    
    await DiagramModel.create_diagram(
        name="Процесс запоминания опыта",
        description="Диаграмма последовательности процесса запоминания опыта в системе АМИ",
        diagram_type="sequence",
        content=memory_sequence,
        is_json=True
    )
    
    logger.info("Тестовые диаграммы успешно добавлены")

def run_init():
    """
    Запускает процесс инициализации базы данных.
    """
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(init_database())
        logger.info("Инициализация базы данных завершена успешно")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {str(e)}")
        sys.exit(1)
    finally:
        loop.close()

if __name__ == "__main__":
    run_init()