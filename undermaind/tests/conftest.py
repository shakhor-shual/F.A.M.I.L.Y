"""
Общие фикстуры для тестирования подсистемы памяти АМИ.
"""

import os
import pytest
import tempfile
import dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, clear_mappers

from undermaind.core.base import Base, create_base
from undermaind.models import setup_relationships
from undermaind.utils.db_init import DatabaseInitializer
from undermaind.utils.ami_init import AmiInitializer


# Загружаем тестовую конфигурацию из test_config.env
test_config_path = os.path.join(os.path.dirname(__file__), 'test_config.env')
dotenv.load_dotenv(test_config_path)


@pytest.fixture(scope="session")
def db_config():
    """Конфигурация для тестовой базы данных."""
    ami_user = os.environ.get("FAMILY_AMI_USER", "ami_test_user")
    return {
        "DB_NAME": os.environ.get("FAMILY_DB_NAME", "family_db"),
        "DB_USER": ami_user,
        "DB_SCHEMA": ami_user,  # Используем имя АМИ как имя схемы
        "DB_PASSWORD": os.environ.get("FAMILY_AMI_PASSWORD", "ami_secure_password"),
        "DB_HOST": os.environ.get("FAMILY_DB_HOST", "localhost"),
        "DB_PORT": os.environ.get("FAMILY_DB_PORT", "5432"),
        "DB_ADMIN_USER": os.environ.get("FAMILY_ADMIN_USER", "family_admin"),
        "DB_ADMIN_PASSWORD": os.environ.get("FAMILY_ADMIN_PASSWORD", "Cold68#Fire"),
    }


@pytest.fixture(scope="session", autouse=True)
def setup_base_model_schema(db_config):
    """
    Инициализирует базовую модель с правильной схемой для тестов.
    Эта фикстура автоматически применяется ко всем тестам в сессии.
    """
    # Сохраняем оригинальный метаданные
    original_metadata = Base.metadata
    original_schema = original_metadata.schema
    
    # Устанавливаем правильную схему для тестов
    Base.metadata.schema = db_config["DB_SCHEMA"]
    
    yield
    
    # Восстанавливаем оригинальную схему после тестов
    Base.metadata.schema = original_schema


@pytest.fixture(scope="session")
def test_engine_memory():
    """Создает SQLite базу в памяти для быстрых тестов без PostgreSQL."""
    engine = create_engine('sqlite:///:memory:')
    
    @event.listens_for(engine, "connect")
    def do_connect(dbapi_connection, connection_record):
        # Включение поддержки внешних ключей для SQLite
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
    
    # Создаем все таблицы
    Base.metadata.create_all(engine)
    
    # Устанавливаем отношения
    setup_relationships()
    
    yield engine
    
    # Удаляем все таблицы и очищаем маппинги
    Base.metadata.drop_all(engine)
    clear_mappers()


@pytest.fixture(scope="session")
def test_db_initializer(db_config):
    """Создает инициализатор базы данных для тестов."""
    return DatabaseInitializer(
        db_host=db_config["DB_HOST"],
        db_port=int(db_config["DB_PORT"]),
        db_name=db_config["DB_NAME"],
        admin_user=db_config["DB_ADMIN_USER"],
        admin_password=db_config["DB_ADMIN_PASSWORD"]
    )


@pytest.fixture(scope="session")
def test_ami_initializer(test_db_initializer, db_config):
    """Создает инициализатор АМИ для тестов."""
    return AmiInitializer(
        ami_name=db_config["DB_SCHEMA"],
        ami_password=db_config["DB_PASSWORD"],
        db_host=test_db_initializer.db_host,
        db_port=test_db_initializer.db_port,
        db_name=test_db_initializer.db_name,
        admin_user=test_db_initializer.admin_user,
        admin_password=test_db_initializer.admin_password
    )


@pytest.fixture(scope="module")
def test_engine_postgres(db_config, test_db_initializer, test_ami_initializer):
    """
    Создает PostgreSQL базу для интеграционных тестов.
    Использует DatabaseInitializer и AmiInitializer для правильной инициализации.
    """
    # Инициализируем базу данных, пересоздавая её для чистоты тестов
    test_db_initializer.initialize_database(recreate=True)
    
    # Пересоздаем тестовый экземпляр АМИ
    test_ami_initializer.recreate_ami(force=True)
    
    # Используем схему из конфигурации напрямую
    ami_schema = db_config['DB_SCHEMA']
    
    # Создаем подключение к базе с указанием схемы АМИ
    connection_string = (
        f"postgresql://{db_config['DB_USER']}:{db_config['DB_PASSWORD']}@"
        f"{db_config['DB_HOST']}:{db_config['DB_PORT']}/"
        f"{db_config['DB_NAME']}"
    )
    engine = create_engine(connection_string)
    
    # Устанавливаем схему поиска
    with engine.connect() as conn:
        conn.execute(text(f"SET search_path TO {ami_schema}, public"))
    
    # Устанавливаем отношения
    setup_relationships()
    
    yield engine
    
    # Очистка: удаляем тестовый экземпляр АМИ
    test_ami_initializer.drop_ami(force=True)


@pytest.fixture(scope="function")
def db_session_memory(test_engine_memory):
    """Создает сессию для работы с тестовой базой данных в памяти."""
    Session = sessionmaker(bind=test_engine_memory)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()
    
    # Очищаем все таблицы после каждого теста
    for table in reversed(Base.metadata.sorted_tables):
        test_engine_memory.execute(table.delete())


@pytest.fixture(scope="function")
def db_session_postgres(test_engine_postgres, db_config):
    """Создает сессию для работы с тестовой базой данных PostgreSQL."""
    Session = sessionmaker(bind=test_engine_postgres)
    session = Session()
    
    # Используем схему напрямую из конфигурации
    ami_schema = db_config['DB_SCHEMA']
    session.execute(text(f"SET search_path TO {ami_schema}, public"))
    
    yield session
    
    session.rollback()
    session.close()


def pytest_configure(config):
    """Регистрация пользовательских маркеров pytest."""
    config.addinivalue_line(
        "markers", "integration: маркер для интеграционных тестов, требующих PostgreSQL"
    )