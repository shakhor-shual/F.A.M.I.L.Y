"""
Общие фикстуры для тестирования подсистемы памяти АМИ.
"""

import os
import pytest
import tempfile
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, clear_mappers

from undermaind.core.base import Base
from undermaind.models import setup_relationships


@pytest.fixture(scope="session")
def db_config():
    """Конфигурация для тестовой базы данных."""
    return {
        "DB_NAME": "test_ami_memory",
        "DB_SCHEMA": "ami_memory",
        "DB_USER": os.environ.get("TEST_DB_USER", "postgres"),
        "DB_PASSWORD": os.environ.get("TEST_DB_PASSWORD", ""),
        "DB_HOST": os.environ.get("TEST_DB_HOST", "localhost"),
        "DB_PORT": os.environ.get("TEST_DB_PORT", "5432"),
    }


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


@pytest.fixture(scope="module")
def test_engine_postgres(db_config):
    """Создает временную PostgreSQL базу для тестов, требующих специфичных для PostgreSQL функций."""
    # Создаем временный файл для хранения команд инициализации
    with tempfile.NamedTemporaryFile(suffix='.sql', mode='w+', delete=False) as f:
        # Записываем команды SQL для создания тестовой схемы
        f.write(f"DROP SCHEMA IF EXISTS {db_config['DB_SCHEMA']} CASCADE;\n")
        f.write(f"CREATE SCHEMA {db_config['DB_SCHEMA']};\n")
        # Создаем расширение vector, если его нет
        f.write("CREATE EXTENSION IF NOT EXISTS vector;\n")
        f.flush()
        
        # Выполняем команды для создания схемы
        setup_cmd = f"psql -U {db_config['DB_USER']} -h {db_config['DB_HOST']} -p {db_config['DB_PORT']}"
        if db_config['DB_PASSWORD']:
            os.environ['PGPASSWORD'] = db_config['DB_PASSWORD']
        
        setup_cmd += f" -d {db_config['DB_NAME']} -f {f.name}"
        os.system(setup_cmd)
    
    # Удаляем временный файл
    os.unlink(f.name)
    
    # Создаем подключение к базе с указанием схемы поиска
    engine = create_engine(
        f"postgresql://{db_config['DB_USER']}:{db_config['DB_PASSWORD']}@"
        f"{db_config['DB_HOST']}:{db_config['DB_PORT']}/"
        f"{db_config['DB_NAME']}"
    )
    
    # Устанавливаем схему поиска
    with engine.connect() as conn:
        conn.execute(text(f"SET search_path TO {db_config['DB_SCHEMA']}, public"))
    
    # Создаем все таблицы
    Base.metadata.create_all(engine)
    
    # Устанавливаем отношения
    setup_relationships()
    
    yield engine
    
    # Удаляем все таблицы и схему
    with engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {db_config['DB_SCHEMA']} CASCADE"))


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
def db_session_postgres(test_engine_postgres):
    """Создает сессию для работы с тестовой базой данных PostgreSQL."""
    Session = sessionmaker(bind=test_engine_postgres)
    session = Session()
    
    # Устанавливаем схему поиска для каждой сессии
    session.execute(text(f"SET search_path TO ami_memory, public"))
    
    yield session
    
    session.rollback()
    session.close()
    
    # Очищаем все таблицы после каждого теста
    for table in reversed(Base.metadata.sorted_tables):
        test_engine_postgres.execute(table.delete())


def pytest_configure(config):
    """Регистрация пользовательских маркеров pytest."""
    config.addinivalue_line(
        "markers", "integration: маркер для интеграционных тестов, требующих PostgreSQL"
    )