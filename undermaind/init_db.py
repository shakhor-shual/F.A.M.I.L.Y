"""
Модуль инициализации базы данных F.A.M.I.L.Y.
"""

import logging
import sys
from typing import Dict, Any

from undermaind.utils.db_init import DatabaseInitializer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('init_db')

def init_database(config: Dict[str, Any], recreate: bool = False, refresh_procedures: bool = True) -> bool:
    """
    Инициализирует базу данных с заданной конфигурацией.
    
    Args:
        config: Словарь с конфигурацией, содержащий:
            - db_host: Хост базы данных
            - db_port: Порт базы данных
            - db_name: Имя базы данных
            - admin_user: Имя администратора БД
            - admin_password: Пароль администратора БД
        recreate: Если True, пересоздает базу данных
        refresh_procedures: Если True, обновляет хранимые процедуры
    
    Returns:
        bool: True если база данных успешно инициализирована, иначе False
    """
    # Создаем инициализатор базы данных
    db_init = DatabaseInitializer(
        db_host=config['db_host'],
        db_port=config['db_port'],
        db_name=config['db_name'],
        admin_user=config['admin_user'],
        admin_password=config['admin_password']
    )
    
    # Проверяем подключение к БД
    if not db_init.check_connection():
        logger.error("Не удалось подключиться к базе данных")
        return False
    
    # Проверяем существование БД и создаём при необходимости
    if not db_init.database_exists():
        logger.info(f"База данных {config['db_name']} не существует, создаём...")
        if not db_init.create_database():
            logger.error(f"Не удалось создать базу данных {config['db_name']}")
            return False
        logger.info(f"База данных {config['db_name']} успешно создана")
    
    # Инициализируем базу данных
    logger.info("Инициализируем базу данных...")
    if not db_init.initialize_database(recreate=recreate, refresh_procedures=refresh_procedures):
        logger.error("Не удалось инициализировать базу данных")
        return False
    
    logger.info("База данных успешно инициализирована")
    return True

if __name__ == '__main__':
    # Для запуска из командной строки используем тестовую конфигурацию
    test_config = {
        'db_host': 'localhost',
        'db_port': 5432,
        'db_name': 'family_db',
        'admin_user': 'family_admin',
        'admin_password': 'Cold68#Fire'
    }
    success = init_database(test_config)
    sys.exit(0 if success else 1) 