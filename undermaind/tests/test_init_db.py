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

def test_init_database(db_config: Dict[str, Any]):
    """
    Тестирует инициализацию базы данных.
    
    Args:
        db_config: Конфигурация базы данных из фикстуры
    """
    logger.info("Начинаем тестирование инициализации базы данных")
    
    # Подготавливаем конфигурацию с правильными ключами
    init_config = {
        'db_host': db_config['host'],
        'db_port': db_config['port'],
        'db_name': db_config['database'],
        'admin_user': db_config['admin_user'],
        'admin_password': db_config['admin_password']
    }
    
    # Инициализируем базу данных
    init_database(
        init_config,
        recreate=db_config.get('recreate', False),
        refresh_procedures=db_config.get('refresh_procedures', True)
    )
    
    logger.info("Тестирование инициализации базы данных завершено") 