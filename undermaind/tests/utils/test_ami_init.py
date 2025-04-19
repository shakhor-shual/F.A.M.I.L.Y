"""
Модуль для тестирования инициализации АМИ (Artificial Mind Identity).
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

logger = logging.getLogger('test_ami_init')

def test_ami_initialization(test_config: Dict[str, Any]) -> None:
    """
    Тестирует инициализацию АМИ с заданной конфигурацией.
    
    Args:
        test_config: Словарь с конфигурацией, содержащий:
            - ami_name: Имя пользователя АМИ
            - ami_password: Пароль пользователя АМИ
            - db_host: Хост базы данных
            - db_port: Порт базы данных
            - db_name: Имя базы данных
            - admin_user: Имя администратора БД
            - admin_password: Пароль администратора БД
    """
    # Создаем инициализатор АМИ
    ami_init = AmiInitializer(
        ami_name=test_config['ami_name'],
        ami_password=test_config['ami_password'],
        db_host=test_config['db_host'],
        db_port=test_config['db_port'],
        db_name=test_config['db_name'],
        admin_user=test_config['admin_user'],
        admin_password=test_config['admin_password']
    )
    
    # Удаляем существующую АМИ если есть
    if ami_init.ami_exists():
        logger.info(f"Удаляем существующую АМИ {test_config['ami_name']}")
        assert ami_init.drop_ami(force=True), "Не удалось удалить существующую АМИ"
    
    # Создаем новую АМИ
    logger.info(f"Создаем новую АМИ {test_config['ami_name']}")
    assert ami_init.create_ami(), "Не удалось создать АМИ"
    
    logger.info("АМИ успешно создана")
    
    # В конце теста удаляем созданную схему
    logger.info(f"Удаляем АМИ {test_config['ami_name']} в конце теста")
    assert ami_init.drop_ami(force=True), "Не удалось удалить АМИ в конце теста"
    
    logger.info("АМИ успешно удалена в конце теста") 