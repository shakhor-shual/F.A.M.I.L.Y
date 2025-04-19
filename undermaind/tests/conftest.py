"""
Централизованная конфигурация для всех тестов в проекте F.A.M.I.L.Y.
"""

import os
import sys
import logging
import pytest
from pathlib import Path
from dotenv import load_dotenv

from undermaind.config import Config, get_config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Устанавливаем режим тестирования
os.environ["FAMILY_TEST_MODE"] = "true"

@pytest.fixture(scope="session")
def test_config():
    """Фикстура для получения конфигурации тестов."""
    config = get_config(reload=True)  # Принудительно перезагружаем конфигурацию
    return {
        'db_host': config.db_host,
        'db_port': config.db_port,
        'db_name': config.db_name,
        'admin_user': config.admin_user,
        'admin_password': config.admin_password,
        'ami_name': config.ami_name,
        'ami_password': config.ami_password,
        'schema': config.schema
    }

@pytest.fixture(scope="session")
def db_initializer(test_config):
    """Фикстура для инициализации базы данных."""
    from undermaind.utils.db_init import DatabaseInitializer
    return DatabaseInitializer(**test_config)

@pytest.fixture(scope="function")
def ami_initializer(test_config):
    """Фикстура для инициализации AMI."""
    from undermaind.utils.ami_init import AmiInitializer
    import uuid
    
    # Генерируем уникальное имя для тестового AMI
    test_ami_name = f"test_ami_{uuid.uuid4().hex[:8]}"
    test_ami_password = test_config['ami_password']
    
    return AmiInitializer(
        ami_name=test_ami_name,
        ami_password=test_ami_password,
        db_host=test_config['db_host'],
        db_port=test_config['db_port'],
        db_name=test_config['db_name'],
        admin_user=test_config['admin_user'],
        admin_password=test_config['admin_password']
    ) 