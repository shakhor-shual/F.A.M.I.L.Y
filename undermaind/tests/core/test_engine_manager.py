"""
Тесты для модуля engine_manager.
"""

import pytest
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine

from undermaind.core.engine_manager import get_engine_manager
from undermaind.config import Config
from undermaind.utils.ami_init import AmiInitializer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="function")
def clean_ami(db_config, ami_config):
    """
    Фикстура для пересоздания AMI перед тестом.
    
    Args:
        db_config: Конфигурация базы данных из фикстуры
        ami_config: Конфигурация AMI из фикстуры
    """
    ami_initializer = AmiInitializer(
        ami_name=ami_config['ami_name'],
        ami_password=ami_config['ami_password'],
        db_host=db_config['host'],
        db_port=int(db_config['port']),
        db_name=db_config['database'],
        admin_user=db_config['admin_user'],
        admin_password=db_config['admin_password']
    )
    
    # Пересоздаем AMI
    ami_initializer.recreate_ami(force=True)
    
    return ami_initializer

def test_engine_caching(db_config, ami_config, clean_ami):
    """
    Тест кэширования движков SQLAlchemy.
    
    Args:
        db_config: Конфигурация базы данных из фикстуры
        ami_config: Конфигурация AMI из фикстуры
        clean_ami: Фикстура для пересоздания AMI
    """
    # Создаем конфигурацию для engine_manager
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
    
    # Получаем первый движок
    engine1 = get_engine_manager(engine_config).get_engine(
        ami_name=ami_config['ami_name'],
        ami_password=ami_config['ami_password'],
        auto_create=True
    )
    
    # Получаем второй движок с теми же параметрами
    engine2 = get_engine_manager(engine_config).get_engine(
        ami_name=ami_config['ami_name'],
        ami_password=ami_config['ami_password'],
        auto_create=True
    )
    
    # Проверяем, что это тот же самый движок (кэшированный)
    assert engine1 is engine2, "Движки с одинаковыми параметрами должны быть одним и тем же объектом"
    
    # Проверяем, что движок работает
    with engine1.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1

def test_ami_table_access_permissions(ami_engine, db_config):
    """
    Тест проверяет права доступа AMI к таблицам в своей схеме.
    
    Args:
        ami_engine: Фикстура движка для работы с AMI
        db_config: Фикстура с конфигурацией базы данных
    """
    # Получаем engine_manager
    engine_manager = get_engine_manager()
    
    # Проверяем текущую схему и доступные таблицы
    with ami_engine.connect() as conn:
        # Проверяем текущую схему
        schema = conn.execute(text("SELECT current_schema()")).scalar()
        assert schema == db_config['schema'], f"Неверная схема: {schema}"
        
        # Проверяем существующие таблицы в схеме AMI
        tables = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = current_schema()
        """)).all()
        
        table_names = [row[0] for row in tables]
        assert len(table_names) > 0, "Схема AMI не содержит таблиц"
        
        # Проверяем, что AMI действительно НЕ имеет прав на создание таблиц
        try:
            conn.execute(text("""
                CREATE TABLE test_create_table_permission (id INTEGER PRIMARY KEY)
            """))
            conn.commit()
            assert False, "AMI смог создать таблицу, хотя не должен иметь таких прав"
        except SQLAlchemyError:
            # Ожидаемая ошибка - у AMI нет прав на создание таблиц
            pass

def test_invalid_credentials(ami_engine, db_config, ami_config):
    """
    Тест обработки неверных учетных данных при подключении к AMI.
    
    Args:
        ami_engine: Фикстура движка для работы с AMI
        db_config: Фикстура с конфигурацией базы данных
        ami_config: Фикстура с конфигурацией AMI
    """
    # Создаем конфигурацию для engine_manager
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
    
    # Создаем менеджер движков с конфигурацией
    engine_manager = get_engine_manager(engine_config)
    
    # Пытаемся получить движок с неверным паролем
    try:
        invalid_engine = engine_manager.get_engine(
            ami_name=ami_config['ami_name'],
            ami_password="wrong_password",
            auto_create=False
        )
        
        # Пробуем выполнить запрос - здесь должна произойти ошибка аутентификации
        with invalid_engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()
            assert False, "Запрос выполнился без исключения при неверном пароле"
    except SQLAlchemyError:
        # Ожидаемая ошибка аутентификации
        pass
    
    # Проверяем, что при правильных учетных данных всё работает
    with ami_engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1, "Запрос с правильными учетными данными не выполнился"

def test_auto_create_with_errors(db_config, ami_config):
    """
    Тест автоматического создания AMI с симуляцией ошибок.
    
    Args:
        db_config: Фикстура с конфигурацией базы данных
        ami_config: Фикстура с конфигурацией AMI
    """
    # Создаем конфигурацию для engine_manager
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
    
    # Создаем менеджер движков с конфигурацией
    engine_manager = get_engine_manager(engine_config)
    
    # Пытаемся получить движок для несуществующего AMI без auto_create
    try:
        engine = engine_manager.get_engine(
            ami_name="nonexistent_ami",
            ami_password="test_password",
            auto_create=False
        )
        
        # Пробуем выполнить запрос - здесь должна произойти ошибка
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()
            assert False, "Запрос выполнился без исключения для несуществующего AMI"
    except SQLAlchemyError:
        # Ожидаемая ошибка - AMI не существует
        pass 