"""
Общие фикстуры для тестирования системы памяти АМИ.

ВНИМАНИЕ: В проекте F.A.M.I.L.Y. используется стандартизированный подход к тестированию.
Перед созданием новых фикстур ОБЯЗАТЕЛЬНО ознакомьтесь с существующими фикстурами
в этом файле и используйте их.

Структура фикстур:
1. db_config - базовая конфигурация тестовой базы данных
2. setup_base_model_schema - настройка схемы для моделей SQLAlchemy
3. test_db_initializer - инициализатор базы данных для тестов
4. test_ami_initializer - инициализатор экземпляра АМИ для тестов
5. test_engine_postgres - движок PostgreSQL для интеграционных тестов
6. db_session_postgres - сессия PostgreSQL для тестов функционального уровня

Для написания новых тестов:
- Для unit-тестов без БД: не требуются особые фикстуры
- Для тестов с БД: используйте db_session_postgres
- Для интеграционных тестов: пометьте тест маркером @pytest.mark.integration
"""

import os
import pytest
import tempfile
import dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, clear_mappers

from undermaind.core.base import Base, create_base
from undermaind.models import setup_relationships
from undermaind.utils.db_init import DatabaseInitializer
from undermaind.utils.ami_init import AmiInitializer


# Загружаем тестовую конфигурацию из корня проекта
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
test_config_path = os.path.join(project_root, "family_config_test.env")
dotenv.load_dotenv(test_config_path)

# Устанавливаем флаг тестового режима
os.environ["FAMILY_TEST_MODE"] = "true"


@pytest.fixture(scope="session")
def db_config():
    """
    Базовая конфигурация тестовой базы данных.
    
    Эта фикстура является основой для всех тестов, взаимодействующих с базой данных.
    Она загружает настройки из тестовой конфигурации и предоставляет их в удобном формате.
    
    Returns:
        dict: Словарь с параметрами подключения к тестовой базе данных
    """
    ami_user = os.environ.get("FAMILY_AMI_USER", "ami_test_user")
    return {
        "DB_NAME": os.environ.get("FAMILY_DB_NAME", "family_db"),
        "DB_USER": ami_user,
        "DB_SCHEMA": ami_user,  # Используем имя пользователя АМИ как имя схемы
        "DB_PASSWORD": os.environ.get("FAMILY_AMI_PASSWORD", "ami_secure_password"),
        "DB_HOST": os.environ.get("FAMILY_DB_HOST", "localhost"),
        "DB_PORT": os.environ.get("FAMILY_DB_PORT", "5432"),
        "DB_ADMIN_USER": os.environ.get("FAMILY_ADMIN_USER", "family_admin"),
        "DB_ADMIN_PASSWORD": os.environ.get("FAMILY_ADMIN_PASSWORD", "Cold68#Fire"),
    }


@pytest.fixture(scope="session", autouse=True)
def setup_base_model_schema(db_config):
    """
    Настраивает базовую модель с правильной схемой для тестов.
    
    Автоматически применяется ко всем тестам в сессии через autouse=True.
    Устанавливает схему из db_config для всех моделей SQLAlchemy.
    
    Args:
        db_config: Конфигурация базы данных (из фикстуры db_config)
    """
    # Сохраняем оригинальные метаданные
    original_metadata = Base.metadata
    original_schema = original_metadata.schema
    
    # Устанавливаем корректную схему для тестов
    Base.metadata.schema = db_config["DB_SCHEMA"]
    
    yield
    
    # Восстанавливаем оригинальную схему после тестов
    Base.metadata.schema = original_schema


@pytest.fixture(scope="session")
def test_db_initializer(db_config):
    """
    Создает инициализатор базы данных для тестов.
    
    Предоставляет объект DatabaseInitializer для управления тестовой БД,
    но не создает саму базу данных. Это делает test_engine_postgres.
    
    Args:
        db_config: Конфигурация базы данных (из фикстуры db_config)
    
    Returns:
        DatabaseInitializer: Инициализатор базы данных для тестов
    """
    return DatabaseInitializer(
        db_host=db_config["DB_HOST"],
        db_port=int(db_config["DB_PORT"]),
        db_name=db_config["DB_NAME"],
        admin_user=db_config["DB_ADMIN_USER"],
        admin_password=db_config["DB_ADMIN_PASSWORD"]
    )


@pytest.fixture(scope="session")
def test_ami_initializer(test_db_initializer, db_config):
    """
    Создает инициализатор АМИ для тестов.
    
    Предоставляет объект AmiInitializer для управления тестовым экземпляром АМИ,
    но не создает сам экземпляр. Это делает test_engine_postgres.
    
    Args:
        test_db_initializer: Инициализатор БД (из фикстуры test_db_initializer)
        db_config: Конфигурация БД (из фикстуры db_config)
    
    Returns:
        AmiInitializer: Инициализатор АМИ для тестов
    """
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
    Создает PostgreSQL-движок для интеграционных тестов.
    
    Эта фикстура:
    1. Инициализирует тестовую базу данных (при необходимости пересоздает её)
    2. Создает тестовый экземпляр АМИ (с собственной схемой)
    3. Настраивает соединение с базой данных
    4. После завершения тестов удаляет тестовый экземпляр АМИ
    
    Имеет scope="module", чтобы каждый модуль тестов получал свежую БД,
    но тесты внутри модуля использовали одну и ту же БД для ускорения.
    
    Args:
        db_config: Конфигурация БД (из фикстуры db_config)
        test_db_initializer: Инициализатор БД (из фикстуры test_db_initializer)
        test_ami_initializer: Инициализатор АМИ (из фикстуры test_ami_initializer)
    
    Returns:
        Engine: SQLAlchemy движок для работы с PostgreSQL
    """
    # Инициализируем базу данных, при необходимости пересоздавая её
    test_db_initializer.initialize_database(recreate=True)
    
    # Пересоздаем тестовый экземпляр АМИ
    test_ami_initializer.recreate_ami(force=True)
    
    # Используем схему напрямую из конфигурации
    ami_schema = db_config['DB_SCHEMA']
    
    # Создаем соединение с базой данных с указанием схемы АМИ
    connection_string = (
        f"postgresql://{db_config['DB_USER']}:{db_config['DB_PASSWORD']}@"
        f"{db_config['DB_HOST']}:{db_config['DB_PORT']}/"
        f"{db_config['DB_NAME']}"
    )
    engine = create_engine(connection_string)
    
    # Устанавливаем путь поиска
    with engine.connect() as conn:
        conn.execute(text(f"SET search_path TO {ami_schema}, public"))
    
    # Устанавливаем связи между моделями
    setup_relationships()
    
    yield engine
    
    # Очистка: удаляем тестовый экземпляр АМИ
    test_ami_initializer.drop_ami(force=True)


@pytest.fixture(scope="function")
def db_session_postgres(test_engine_postgres, db_config):
    """
    Создает сессию для работы с тестовой базой данных PostgreSQL.
    
    ОСНОВНАЯ ФИКСТУРА ДЛЯ ТЕСТОВ С БАЗОЙ ДАННЫХ.
    Используйте эту фикстуру для всех тестов, которым требуется 
    взаимодействие с базой данных.
    
    Каждый тест получает чистую изолированную сессию. Изменения,
    сделанные в одном тесте, не влияют на другие тесты.
    
    Пример использования:
    ```python
    def test_something(db_session_postgres):
        # db_session_postgres - это сессия SQLAlchemy для работы с БД
        entity = Entity(name="test")
        db_session_postgres.add(entity)
        db_session_postgres.commit()
        
        # Проверка результата
        assert db_session_postgres.query(Entity).filter_by(name="test").first() is not None
    ```
    
    Args:
        test_engine_postgres: Движок PostgreSQL (из фикстуры test_engine_postgres)
        db_config: Конфигурация базы данных (из фикстуры db_config)
    
    Returns:
        Session: Сессия SQLAlchemy для работы с PostgreSQL
    """
    Session = sessionmaker(bind=test_engine_postgres)
    session = Session()
    
    # Используем схему напрямую из конфигурации
    ami_schema = db_config['DB_SCHEMA']
    session.execute(text(f"SET search_path TO {ami_schema}, public"))
    
    yield session
    
    # Откатываем незавершенные транзакции и закрываем сессию
    session.rollback()
    session.close()


def pytest_configure(config):
    """
    Регистрация пользовательских маркеров pytest.
    
    Маркеры используются для категоризации тестов и выборочного запуска.
    """
    config.addinivalue_line(
        "markers", "integration: маркер для интеграционных тестов, требующих PostgreSQL"
    )