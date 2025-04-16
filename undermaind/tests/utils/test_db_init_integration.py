"""
Интеграционные тесты для DatabaseInitializer.

Проверяет функциональность инициализации базы данных F.A.M.I.L.Y.,
что является критически важным для создания надежной основы хранения памяти АМИ.
"""

import os
import pytest
import logging
import dotenv
from pathlib import Path
import psycopg2
from sqlalchemy import text, inspect

from undermaind.utils.db_init import DatabaseInitializer

# Настройка логирования для тестов
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def test_config_path():
    """Путь к файлу конфигурации для тестовой среды."""
    # Используем стандартный конфигурационный файл из директории tests
    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "test_config.env"
    
    if not config_path.exists():
        pytest.skip(f"Файл конфигурации не найден: {config_path}")
    
    return config_path


@pytest.fixture(scope="module")
def db_initializer(test_config_path):
    """Создает экземпляр DatabaseInitializer для тестов."""
    # Загружаем конфигурацию из тестового файла
    dotenv.load_dotenv(test_config_path)
    
    return DatabaseInitializer(
        db_host=os.environ.get("FAMILY_DB_HOST", "localhost"),
        db_port=int(os.environ.get("FAMILY_DB_PORT", "5432")),
        db_name=os.environ.get("FAMILY_DB_NAME", "family_db"),
        admin_user=os.environ.get("FAMILY_ADMIN_USER", "family_admin"),
        admin_password=os.environ.get("FAMILY_ADMIN_PASSWORD"),
    )


@pytest.mark.integration
class TestDatabaseInitializerIntegration:
    """
    Интеграционные тесты для DatabaseInitializer.
    
    Проверяет создание БД, пользователя-администратора и применение SQL скриптов
    в реальном окружении PostgreSQL.
    """
    
    def test_load_config(self, test_config_path):
        """Проверяет загрузку конфигурации из файла."""
        initializer = DatabaseInitializer(config_path=str(test_config_path))
        
        # Проверяем базовые параметры
        assert initializer.db_host == os.environ.get("FAMILY_DB_HOST", "localhost")
        assert initializer.db_port == int(os.environ.get("FAMILY_DB_PORT", "5432"))
        assert initializer.db_name == os.environ.get("FAMILY_DB_NAME", "family_db")
        assert initializer.admin_user == os.environ.get("FAMILY_ADMIN_USER", "family_admin")
        assert initializer.admin_password == os.environ.get("FAMILY_ADMIN_PASSWORD")

    def test_connection(self, db_initializer):
        """Проверяет возможность подключения к БД."""
        assert db_initializer.check_connection() is True

    def test_database_exists(self, db_initializer):
        """Проверяет определение существования БД."""
        # Проверяем текущее состояние
        initial_exists = db_initializer.database_exists()
        
        if initial_exists:
            # Если БД существует, удаляем для теста
            assert db_initializer.drop_database(force=True) is True
            assert db_initializer.database_exists() is False
            
            # Восстанавливаем БД
            assert db_initializer.create_database() is True
            assert db_initializer.database_exists() is True
        else:
            # Если БД не существует, создаем
            assert db_initializer.create_database() is True
            assert db_initializer.database_exists() is True

    def test_create_admin_user(self, db_initializer):
        """Проверяет создание пользователя-администратора."""
        # Создаем пользователя
        assert db_initializer.create_admin_user() is True
        
        # Проверяем что пользователь существует через прямое подключение
        with db_initializer._get_postgres_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s",
                    (db_initializer.admin_user,)
                )
                assert cur.fetchone() is not None

    def test_database_recreation(self, db_initializer):
        """Проверяет пересоздание базы данных."""
        # Сначала убеждаемся что БД существует
        if not db_initializer.database_exists():
            assert db_initializer.create_database() is True
        
        # Пробуем пересоздать
        assert db_initializer.initialize_database(recreate=True) is True
        assert db_initializer.database_exists() is True
        
        # Проверяем через прямое подключение что БД доступна
        with db_initializer._get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                assert cur.fetchone() is not None

    def test_apply_sql_scripts(self, db_initializer):
        """Проверяет применение SQL скриптов."""
        # Инициализируем чистую БД
        assert db_initializer.initialize_database(recreate=True) is True
        
        # Применяем скрипты уровня consciousness_level
        result = db_initializer.apply_sql_scripts('consciousness_level')
        assert result is True
        
        # Проверяем что основные объекты созданы через прямое подключение
        with db_initializer._get_database_connection() as conn:
            with conn.cursor() as cur:
                # Проверяем существование процедуры init_ami_consciousness_level
                cur.execute("""
                    SELECT 1 FROM pg_proc p 
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = 'public' 
                    AND p.proname = 'init_ami_consciousness_level'
                """)
                assert cur.fetchone() is not None

    def test_database_initialization(self, db_initializer):
        """Проверяет полный процесс инициализации БД."""
        # Удаляем БД если существует
        if db_initializer.database_exists():
            assert db_initializer.drop_database(force=True) is True
        
        # Инициализируем с нуля
        assert db_initializer.initialize_database() is True
        
        # Проверяем что БД создана
        assert db_initializer.database_exists() is True
        
        # Проверяем что административный пользователь существует
        with db_initializer._get_postgres_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s",
                    (db_initializer.admin_user,)
                )
                assert cur.fetchone() is not None
        
        # Проверяем что основные объекты созданы
        with db_initializer._get_database_connection() as conn:
            with conn.cursor() as cur:
                # Проверяем существование публичной схемы
                cur.execute("SELECT 1 FROM pg_namespace WHERE nspname = 'public'")
                assert cur.fetchone() is not None