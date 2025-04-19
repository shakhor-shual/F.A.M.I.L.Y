"""
Общие фикстуры для тестов F.A.M.I.L.Y.

Этот модуль содержит фикстуры, используемые во всех тестах проекта.
"""

import os
import logging
import pytest
import uuid
import dotenv
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, clear_mappers
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from typing import Dict, Any

from undermaind.core.base import Base
from undermaind.models import setup_relationships
from undermaind.core.engine_manager import get_engine_manager
from undermaind.utils.ami_init import AmiInitializer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('test_context')

def load_test_config() -> Dict[str, Any]:
    """
    Загружает конфигурацию для тестов из .env файла.
    
    Returns:
        Dict[str, Any]: Словарь с конфигурацией для тестов
    """
    # Загружаем настройки из .env файла
    env_path = Path(__file__).parent.parent.parent / 'family_config.env'
    load_dotenv(env_path)
    
    # Получаем настройки из переменных окружения
    config = {
        'db_host': os.getenv('FAMILY_DB_HOST'),
        'db_port': int(os.getenv('FAMILY_DB_PORT', '5432')),
        'db_name': os.getenv('FAMILY_DB_NAME'),
        'admin_user': os.getenv('FAMILY_ADMIN_USER'),
        'admin_password': os.getenv('FAMILY_ADMIN_PASSWORD'),
        'ami_name': os.getenv('FAMILY_AMI_USER'),
        'ami_password': os.getenv('FAMILY_AMI_PASSWORD')
    }
    
    return config

@pytest.fixture(scope="session")
def test_config():
    """
    Фикстура для получения конфигурации тестов.
    
    Returns:
        Dict[str, Any]: Словарь с конфигурацией для тестов
    """
    return load_test_config()

@pytest.fixture(scope="session")
def db_config():
    """
    Фикстура для доступа к конфигурации базы данных.
    
    Возвращает словарь с параметрами подключения к БД из переменных окружения.
    
    Returns:
        dict: Словарь с параметрами подключения к БД
    """
    config = {
        'host': os.environ.get('FAMILY_DB_HOST', 'localhost'),
        'port': os.environ.get('FAMILY_DB_PORT', '5432'),
        'database': os.environ.get('FAMILY_DB_NAME', 'family_db'),
        'admin_user': os.environ.get('FAMILY_ADMIN_USER', 'family_admin'),
        'admin_password': os.environ.get('FAMILY_ADMIN_PASSWORD', ''),
        'schema': os.environ.get('FAMILY_AMI_USER', 'ami_test_user'),  # Схема совпадает с именем AMI
        'password': os.environ.get('FAMILY_AMI_PASSWORD', 'ami_secure_password'),  # Пароль AMI
        'recreate': True,
        'refresh_procedures': True
    }
    return config

@pytest.fixture
def ami_config() -> Dict[str, Any]:
    """
    Фикстура с конфигурацией AMI.
    
    Returns:
        Dict[str, Any]: Конфигурация AMI
    """
    return {
        'ami_name': 'test_ami',
        'ami_password': 'test_ami_password'
    }

# Если среда разработки поддерживает переменные окружения .env
# загружаем их из корневой директории проекта
project_root = Path(__file__).parent.parent.parent
env_path = project_root / 'family_config_test.env'
if env_path.exists():
    dotenv.load_dotenv(env_path)
else:
    # Если тестовый env-файл не найден, используем стандартный
    env_path = project_root / 'family_config.env'
    if env_path.exists():
        dotenv.load_dotenv(env_path)

# Set test mode flag
os.environ["FAMILY_TEST_MODE"] = "true"

# Check if required environment variables are set
required_vars = ["FAMILY_DB_NAME", "FAMILY_AMI_USER", "FAMILY_AMI_PASSWORD", 
                "FAMILY_ADMIN_USER", "FAMILY_ADMIN_PASSWORD"]
missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.warning("Tests that depend on database connections may fail.")


@pytest.fixture(scope="session", autouse=True)
def setup_base_model_schema(db_config):
    """
    Sets up the base model with the correct schema for tests.
    
    Automatically applied to all tests in the session via autouse=True.
    Sets the schema from db_config for all SQLAlchemy models.
    
    Args:
        db_config: Database configuration (from db_config fixture)
    """
    # Save original metadata
    original_metadata = Base.metadata
    original_schema = original_metadata.schema
    
    # Set the correct schema for tests
    Base.metadata.schema = db_config["schema"]
    
    yield
    
    # Restore original schema after tests
    Base.metadata.schema = original_schema


@pytest.fixture(scope="module")
def ami_engine(db_config, request):
    """
    Универсальная фикстура для работы с памятью АМИ через SQLAlchemy Engine.
    
    Эта фикстура обеспечивает полную интеграцию с принципом "непрерывности бытия" АМИ:
    1. Автоматически создает базу данных при необходимости
    2. Автоматически создает АМИ и схему если они не существуют
    3. Настраивает все необходимые параметры подключения
    4. Очищает тестовые данные после выполнения тестов
    
    Параметры можно настроить через маркер 'ami_params':
    @pytest.mark.parametrize('ami_params', [{'unique': True}], indirect=True)
    
    Args:
        db_config: Configuration dictionary
        request: pytest request object for accessing markers
        
    Returns:
        Engine: SQLAlchemy engine for database operations
        
    Note:
        По умолчанию использует АМИ из конфигурации, но можно запросить
        уникальный АМИ для тестов через маркер ami_params с параметром unique=True
    """
    # Проверяем наличие маркера с параметрами
    params = {}
    if hasattr(request, 'param'):
        params = request.param
        
    # Если запрошено уникальное АМИ для тестов, генерируем уникальное имя
    if params.get('unique'):
        ami_name = f"test_ami_{uuid.uuid4().hex[:8]}"
        ami_password = f"test_pwd_{uuid.uuid4().hex[:8]}"
    else:
        # Используем АМИ из тестовой конфигурации
        ami_name = db_config["schema"]
        ami_password = db_config["password"]
    
    # Получаем движок управления памятью
    engine_manager = get_engine_manager()
    
    # Получаем движок для работы с АМИ (создаст АМИ если необходимо)
    engine = engine_manager.get_engine(
        ami_name=ami_name,
        ami_password=ami_password,
        auto_create=True  # Автоматически создает АМИ при необходимости
    )
    
    # Настраиваем модели
    setup_relationships()
    
    # Запоминаем в контексте имя АМИ для дальнейшего использования
    request.node.ami_name = ami_name
    request.node.ami_password = ami_password
    
    # Логируем информацию о созданном АМИ
    if params.get('unique'):
        logger.info(f"Created temporary unique AMI: {ami_name}")
    
    yield engine
    
    # Очистка: если использовался уникальный АМИ, удаляем его
    if params.get('unique'):
        try:
            ami_initializer = AmiInitializer(
                ami_name=ami_name,
                ami_password=ami_password,
                db_host=db_config["host"],
                db_port=int(db_config["port"]),
                db_name=db_config["database"],
                admin_user=db_config["admin_user"],
                admin_password=db_config["admin_password"]
            )
            ami_initializer.drop_ami(force=True)
            logger.info(f"Removed temporary AMI: {ami_name}")
        except Exception as e:
            logger.error(f"Error removing temporary AMI {ami_name}: {e}")


@pytest.fixture(scope="function")
def db_session(ami_engine):
    """
    Creates a session for working with the PostgreSQL test database.
    
    MAIN FIXTURE FOR DATABASE TESTS.
    Use this fixture for all tests that require 
    interaction with the database.
    
    Each test gets a clean isolated session. Changes
    made in one test do not affect other tests.
    
    Args:
        ami_engine: SQLAlchemy engine for database connection
    
    Returns:
        Session: SQLAlchemy session for working with PostgreSQL
    """
    Session = sessionmaker(bind=ami_engine)
    session = Session()
    
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        try:
            session.rollback()  # Roll back any uncommitted changes
            session.close()
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")


@pytest.fixture(scope="module")
def admin_engine(db_config):
    """
    Creates a PostgreSQL engine with administrator privileges for schema and table management.
    
    This fixture provides a SQLAlchemy engine with administrative privileges,
    which is necessary for creating tables, schemas, and managing access rights.
    Use this fixture for tests that need to create or modify database structure.
    
    Args:
        db_config: Database configuration (from db_config fixture)
    
    Returns:
        Engine: SQLAlchemy engine with administrator privileges
    """
    # Create database connection as administrator
    connection_string = (
        f"postgresql://{db_config['admin_user']}:{db_config['admin_password']}@"
        f"{db_config['host']}:{db_config['port']}/"
        f"{db_config['database']}"
    )
    
    engine = create_engine(
        connection_string,
        isolation_level="AUTOCOMMIT",  # Автоматический коммит для предотвращения блокировок
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10}
    )
    
    logger.info(f"Created administrative engine with autocommit mode")
    
    yield engine


@pytest.fixture(scope="module")
def vector_test_env(admin_engine, db_config, request):
    """
    Prepares an environment for testing vector operations with pgvector extension.
    
    This fixture:
    1. Checks if pgvector extension is available
    2. Creates it if not present and if has admin privileges
    3. Provides necessary helper functions for vector tests
    
    Args:
        admin_engine: Admin PostgreSQL engine (from admin_engine fixture)
        db_config: Database configuration (from db_config fixture)
        request: pytest request object for accessing the ami_name
    
    Returns:
        dict: Helper functions and metadata for vector testing
    """
    # Получаем имя АМИ из контекста
    if hasattr(request.node, 'ami_name'):
        ami_schema = request.node.ami_name
    else:
        ami_schema = db_config['schema']
        
    has_pgvector = False
    
    # Check if pgvector extension is available
    try:
        with admin_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
            )).scalar()
            
            has_pgvector = result > 0
            
            # Try to create extension if not present
            if not has_pgvector:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    has_pgvector = True
                    logger.info("Successfully installed pgvector extension")
                except SQLAlchemyError as e:
                    logger.warning(f"Could not create pgvector extension: {e}")
    except SQLAlchemyError as e:
        logger.warning(f"Could not check for pgvector extension: {e}")
    
    # Create test environment
    def create_vector_table(table_name='vector_test_table', vector_dim=3):
        """Create a table for vector testing"""
        if not has_pgvector:
            pytest.skip("pgvector extension not available")
        
        try:
            with admin_engine.connect() as conn:
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {ami_schema}.{table_name} (
                        id SERIAL PRIMARY KEY,
                        embedding VECTOR({vector_dim}),
                        metadata JSONB
                    )
                """))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create vector test table: {e}")
            return False
    
    def drop_vector_table(table_name='vector_test_table'):
        """Drop a vector test table"""
        try:
            with admin_engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {ami_schema}.{table_name}"))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop vector test table: {e}")
            return False
    
    # Return the test environment
    env = {
        'has_pgvector': has_pgvector,
        'create_vector_table': create_vector_table,
        'drop_vector_table': drop_vector_table,
        'ami_schema': ami_schema,
    }
    
    yield env
    
    # Cleanup any test tables that might have been created
    drop_vector_table('vector_test_table')


@pytest.fixture(scope="function")
def ami_params(request):
    """
    Фикстура для генерации параметров АМИ.
    
    Эта фикстура может принимать параметры для настройки создания АМИ:
    * unique (bool): Создать уникальное имя АМИ (по умолчанию False)
    * ami_name (str): Использовать указанное имя АМИ
    * ami_password (str): Использовать указанный пароль АМИ
    
    Args:
        request: Объект запроса pytest с параметрами
    
    Returns:
        dict: Словарь с параметрами АМИ (имя и пароль)
    """
    # По умолчанию создаем тестовое АМИ с фиксированным именем
    params = {
        'ami_name': 'test_ami',
        'ami_password': 'test_password'
    }
    
    # Если запрошено уникальное имя или параметр direct=True
    marker = request.node.get_closest_marker('ami_params')
    if marker:
        if marker.kwargs.get('unique') or getattr(request, 'param', {}).get('unique'):
            unique_id = uuid.uuid4().hex[:8]
            params['ami_name'] = f"test_ami_{unique_id}"
            params['ami_password'] = f"pwd_{unique_id}"
    
    # Если в параметрах есть конкретные значения, используем их
    if hasattr(request, 'param'):
        if request.param.get('ami_name'):
            params['ami_name'] = request.param['ami_name']
        if request.param.get('ami_password'):
            params['ami_password'] = request.param['ami_password']
    
    # Сохраняем значения в контексте запроса для использования в других фикстурах
    request.node.ami_name = params['ami_name']
    request.node.ami_password = params['ami_password']
    
    return params


@pytest.fixture(scope="function")
def temp_db_path(tmp_path):
    """
    Создает временную директорию для тестовых файлов БД.
    
    Args:
        tmp_path: Временная директория pytest
    
    Returns:
        Path: Путь к временной директории для файлов БД
    """
    db_path = tmp_path / "db"
    db_path.mkdir()
    return db_path


def pytest_configure(config):
    """
    Register custom pytest markers.
    
    Markers are used for categorizing tests and selective running.
    """
    config.addinivalue_line(
        "markers", "integration: marker for integration tests requiring PostgreSQL"
    )
    config.addinivalue_line(
        "markers", "functional: marker for functional tests"
    )
    config.addinivalue_line(
        "markers", "unit: marker for unit tests"
    )
    config.addinivalue_line(
        "markers", "vector: marker for tests involving vector operations"
    )
    config.addinivalue_line(
        "markers", "ami_params: marker for passing parameters to ami_engine fixture"
    )