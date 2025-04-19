"""
Модуль для тестирования инициализации AMI.
"""

import logging
import pytest
from typing import Dict, Any

from undermaind.utils.ami_init import AmiInitializer
from undermaind.init_db import init_database
from undermaind.config import Config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('test_ami_init')

def test_ami_initialization(ami_config: Dict[str, Any], db_config: Dict[str, Any]):
    """
    Тестирует инициализацию AMI.
    
    Args:
        ami_config: Конфигурация AMI из фикстуры
        db_config: Конфигурация базы данных из фикстуры
    """
    logger.info("Начинаем тестирование инициализации AMI")
    
    # Подготавливаем конфигурацию для init_database
    init_config = {
        'db_host': db_config['host'],
        'db_port': db_config['port'],
        'db_name': db_config['database'],
        'admin_user': db_config['admin_user'],
        'admin_password': db_config['admin_password']
    }
    
    # Инициализируем базу данных
    logger.info("Инициализируем базу данных")
    init_database(init_config, recreate=True, refresh_procedures=True)
    
    # Создаем инициализатор AMI
    ami_init = AmiInitializer(
        ami_name=ami_config['ami_name'],
        ami_password=ami_config['ami_password'],
        db_host=db_config['host'],
        db_port=int(db_config['port']),
        db_name=db_config['database'],
        admin_user=db_config['admin_user'],
        admin_password=db_config['admin_password']
    )
    
    # Проверяем существование AMI
    exists = ami_init.ami_exists()
    logger.info(f"AMI существует: {exists}")
    
    # Если AMI существует, удаляем его
    if exists:
        ami_init.drop_ami()
        logger.info("Существующий AMI удален")
    
    # Получаем AMI (создаст если не существует)
    success, info = ami_init.get_ami()
    if not success:
        logger.error(f"Не удалось получить/создать AMI: {info['error']}")
        assert False, f"Не удалось получить/создать AMI: {info['error']}"
    
    logger.info("AMI получен/создан")
    
    # Проверяем, что AMI создан успешно
    assert ami_init.ami_exists(), "AMI не был создан"
    assert ami_init.schema_exists(), "Схема AMI не была создана"
    
    logger.info("Тестирование инициализации AMI завершено")

    # Prepare configuration for engine manager
    engine_config = Config(
        DB_HOST=db_config['host'],
        DB_PORT=int(db_config['port']),
        DB_NAME=db_config['database'],
        DB_ADMIN_USER=db_config['admin_user'],
        DB_ADMIN_PASSWORD=db_config['admin_password'],
        DB_USERNAME=ami_config['ami_name'],
        DB_PASSWORD=ami_config['ami_password'],
        DB_SCHEMA=ami_config['ami_name']
    )
    
    from undermaind.core.engine_manager import get_engine_manager
    engine_manager = get_engine_manager(engine_config)
    
    try:
        engine = engine_manager.get_engine(
            ami_name=ami_config['ami_name'],
            ami_password=ami_config['ami_password'],
            auto_create=True
        )
        assert engine is not None, "AMI не был создан"
        logger.info("AMI initialization test completed successfully")
    except Exception as e:
        logger.error(f"Error during AMI initialization: {str(e)}")
        raise 