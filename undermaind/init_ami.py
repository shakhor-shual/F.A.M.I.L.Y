"""
Модуль инициализации АМИ (Artificial Mind Identity).
"""

import logging
import sys
from typing import Dict, Any

from undermaind.utils.ami_init import AmiInitializer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('init_ami')

def init_ami(config: Dict[str, Any], force_recreate: bool = False) -> bool:
    """
    Инициализирует АМИ с заданной конфигурацией.
    
    Args:
        config: Словарь с конфигурацией, содержащий:
            - ami_name: Имя пользователя АМИ
            - ami_password: Пароль пользователя АМИ
            - db_host: Хост базы данных
            - db_port: Порт базы данных
            - db_name: Имя базы данных
            - admin_user: Имя администратора БД
            - admin_password: Пароль администратора БД
        force_recreate: Если True, пересоздает АМИ даже если она уже существует
    
    Returns:
        bool: True если АМИ успешно создан, иначе False
    """
    # Создаем инициализатор АМИ
    ami_init = AmiInitializer(
        ami_name=config['ami_name'],
        ami_password=config['ami_password'],
        db_host=config['db_host'],
        db_port=config['db_port'],
        db_name=config['db_name'],
        admin_user=config['admin_user'],
        admin_password=config['admin_password']
    )
    
    # Проверяем существование АМИ
    if ami_init.ami_exists():
        if force_recreate:
            logger.info(f"Удаляем существующую АМИ {config['ami_name']}")
            if not ami_init.drop_ami(force=True):
                logger.error("Не удалось удалить существующую АМИ")
                return False
        else:
            logger.info(f"АМИ {config['ami_name']} уже существует")
            return True
    
    # Создаем новую АМИ
    logger.info(f"Создаем новую АМИ {config['ami_name']}")
    if not ami_init.create_ami():
        logger.error("Не удалось создать АМИ")
        return False
    
    logger.info("АМИ успешно создана")
    return True 