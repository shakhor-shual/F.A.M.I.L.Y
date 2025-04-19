"""
Модуль для тестирования инициализации базы данных.
"""

import logging
import pytest
from typing import Dict, Any

from undermaind.init_db import init_database

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('test_init_db')

def test_init_database(test_config: Dict[str, Any]):
    """
    Тестирует инициализацию базы данных.
    
    Args:
        test_config: Конфигурация из фикстуры test_config
    """
    logger.info("Начинаем тестирование инициализации базы данных")
    
    # Инициализируем базу данных
    init_database(
        test_config,
        recreate=False,
        refresh_procedures=True
    )
    
    logger.info("Тестирование инициализации базы данных завершено") 