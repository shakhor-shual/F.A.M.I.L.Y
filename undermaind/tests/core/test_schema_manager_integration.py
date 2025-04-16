"""
Интеграционные тесты для SchemaManager.

Этот модуль содержит тесты, проверяющие взаимодействие SchemaManager
с реальной базой данных PostgreSQL с использованием конфигурации из test_config.env.
"""

import os
import pytest
import dotenv
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch

from undermaind.core.schema_manager import SchemaManager, get_schema_manager
from undermaind.config import Config


@pytest.fixture(scope="module")
def test_config_path():
    """Путь к файлу конфигурации для тестовой среды."""
    # Используем файл конфигурации из директории tests
    base_dir = Path(__file__).parent.parent
    return base_dir / "test_config.env"


@pytest.fixture(scope="module")
def test_config(test_config_path):
    """Создает тестовую конфигурацию на основе файла test_config.env."""
    # Проверяем существование файла
    config_path = test_config_path
    if not config_path.exists():
        pytest.skip(f"Файл конфигурации не найден: {config_path}")
    
    # Загружаем переменные окружения из файла
    dotenv.load_dotenv(config_path)
    
    # Создаем конфигурацию из переменных окружения с префиксом FAMILY_
    return Config(
        DB_NAME=os.environ.get("FAMILY_DB_NAME", "family_db"),
        DB_HOST=os.environ.get("FAMILY_DB_HOST", "localhost"),
        DB_PORT=os.environ.get("FAMILY_DB_PORT", "5432"),
        DB_USERNAME=os.environ.get("FAMILY_DB_USERNAME", "family_admin"),
        DB_PASSWORD=os.environ.get("FAMILY_DB_PASSWORD", ""),
        DB_SCHEMA=os.environ.get("FAMILY_DB_SCHEMA", "ami_memory")
    )


@pytest.fixture(scope="module")
def admin_credentials():
    """Получает учетные данные администратора PostgreSQL из переменных окружения."""
    # Используем FAMILY_ADMIN_* переменные из test_config.env
    admin_user = os.environ.get("FAMILY_ADMIN_USER")
    admin_password = os.environ.get("FAMILY_ADMIN_PASSWORD")
    
    # Пропускаем тесты, если учетные данные не предоставлены
    if not admin_user or not admin_password:
        pytest.skip("Не указаны учетные данные администратора (FAMILY_ADMIN_USER/FAMILY_ADMIN_PASSWORD)")
    
    return admin_user, admin_password


@pytest.fixture(scope="module")
def schema_manager(test_config, admin_credentials):
    """Создает экземпляр SchemaManager с установленными учетными данными администратора."""
    admin_user, admin_password = admin_credentials
    manager = SchemaManager(test_config)
    manager.set_admin_credentials(admin_user, admin_password)
    return manager


@pytest.mark.integration
class TestSchemaManagerIntegration:
    """
    Интеграционные тесты для SchemaManager.
    
    Требует доступа к реальной PostgreSQL базе данных с правами администратора
    для создания/удаления схем и пользователей.
    """
    
    # Тестовые данные, используем имя из конфигурации для уникальности
    TEST_SCHEMA = os.environ.get("FAMILY_AMI_SCHEMA", "ami_test_user") + "_schema_test"
    TEST_PASSWORD = os.environ.get("FAMILY_AMI_PASSWORD", "ami_secure_password")
    
    def test_schema_exists(self, schema_manager):
        """Проверяет функцию определения существования схемы."""
        # Предположение: схема public всегда существует в PostgreSQL
        assert schema_manager.schema_exists("public") is True
        # Предположение: схема с именем 'nonexistent_schema_123' не существует
        assert schema_manager.schema_exists("nonexistent_schema_123") is False
    
    def test_create_and_drop_schema(self, schema_manager):
        """Проверяет создание и удаление схемы."""
        try:
            # Удаляем схему, если она осталась от предыдущих тестов
            schema_manager.drop_schema(self.TEST_SCHEMA, cascade=True, drop_user=True)
            
            # Создаем схему с пользователем
            assert schema_manager.create_schema(
                self.TEST_SCHEMA, 
                self.TEST_PASSWORD, 
                create_user=True, 
                grant_permissions=True
            ) is True
            
            # Проверяем, что схема создана
            assert schema_manager.schema_exists(self.TEST_SCHEMA) is True
            
            # Проверяем, что пользователь создан
            assert schema_manager.user_exists(self.TEST_SCHEMA) is True
            
            # Удаляем схему и пользователя
            assert schema_manager.drop_schema(
                self.TEST_SCHEMA, 
                cascade=True, 
                drop_user=True
            ) is True
            
            # Проверяем, что схема удалена
            assert schema_manager.schema_exists(self.TEST_SCHEMA) is False
            
            # Проверяем, что пользователь удален
            assert schema_manager.user_exists(self.TEST_SCHEMA) is False
        
        finally:
            # Гарантированная очистка после теста
            try:
                schema_manager.drop_schema(self.TEST_SCHEMA, cascade=True, drop_user=True)
            except:
                pass
    
    def test_get_schema_manager_factory(self, test_config, admin_credentials):
        """Проверяет фабричную функцию get_schema_manager."""
        admin_user, admin_password = admin_credentials
        
        # Проверяем, что фабрика создает менеджер с правильными учетными данными
        manager = get_schema_manager(
            config=test_config,
            admin_user=admin_user,
            admin_password=admin_password
        )
        
        assert isinstance(manager, SchemaManager)
        assert manager.schema_exists("public") is True
    
    def test_create_engine_for_schema(self, schema_manager):
        """Проверяет создание движка SQLAlchemy для работы с указанной схемой."""
        try:
            # Создаем схему с пользователем
            schema_manager.create_schema(
                self.TEST_SCHEMA, 
                self.TEST_PASSWORD, 
                create_user=True
            )
            
            # Создаем движок с использованием учетных данных пользователя схемы
            engine = schema_manager.create_engine_for_schema(
                self.TEST_SCHEMA,
                self.TEST_PASSWORD
            )
            
            # Проверяем, что движок создан и может подключиться к БД
            with engine.connect() as conn:
                # Выполняем простой запрос
                result = conn.execute(text("SELECT 1 as result")).scalar()
                assert result == 1
            
            # Тестируем создание движка с правами администратора
            admin_engine = schema_manager.create_engine_for_schema(
                self.TEST_SCHEMA,
                use_admin=True
            )
            
            # Проверяем, что движок создан и может подключиться к БД
            with admin_engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as result")).scalar()
                assert result == 1
        
        finally:
            # Гарантированная очистка после теста
            schema_manager.drop_schema(self.TEST_SCHEMA, cascade=True, drop_user=True)
    
    def test_initialize_ami_memory(self, schema_manager, monkeypatch):
        """
        Проверяет инициализацию схемы памяти АМИ из SQL-скриптов.
        
        Этот тест использует патч для execute_sql_script, чтобы не выполнять
        фактические SQL-скрипты в тестовой среде.
        """
        test_schema = "test_ami_memory_init"
        
        try:
            # Патчим метод execute_sql_script, чтобы он всегда возвращал True
            with patch.object(schema_manager, 'execute_sql_script', return_value=True):
                # Инициализируем схему
                result = schema_manager.initialize_ami_memory(
                    test_schema,
                    "test_password"
                )
                
                # Проверяем результат
                assert result is True
                
                # Проверяем, что схема создана
                assert schema_manager.schema_exists(test_schema) is True
        
        finally:
            # Гарантированная очистка после теста
            schema_manager.drop_schema(test_schema, cascade=True, drop_user=True)
    
    def test_execute_sql_script(self, schema_manager, tmp_path):
        """
        Проверяет выполнение SQL-скриптов.
        
        Создает временный SQL-скрипт и выполняет его через SchemaManager.
        """
        test_schema = "test_script_execution"
        
        try:
            # Создаем схему
            schema_manager.create_schema(test_schema, "test_password")
            
            # Создаем временный SQL-скрипт
            script_path = tmp_path / "test_script.sql"
            with open(script_path, "w") as f:
                f.write(f"-- Тестовый SQL-скрипт\n")
                f.write(f"CREATE TABLE IF NOT EXISTS {test_schema}.test_table (\n")
                f.write(f"    id SERIAL PRIMARY KEY,\n")
                f.write(f"    name TEXT NOT NULL\n")
                f.write(f");\n")
            
            # Выполняем скрипт
            result = schema_manager.execute_sql_script(
                str(script_path),
                test_schema
            )
            
            # Проверяем результат
            assert result is True
            
            # Проверяем, что таблица создана
            with schema_manager.admin_engine.connect() as conn:
                inspector = inspect(schema_manager.admin_engine)
                assert "test_table" in inspector.get_table_names(schema=test_schema)
        
        finally:
            # Гарантированная очистка после теста
            schema_manager.drop_schema(test_schema, cascade=True, drop_user=True)
    
    def test_create_database(self, schema_manager):
        """Проверяет создание базы данных, если она не существует."""
        try:
            # Создаем временную базу данных для теста
            test_db_name = f"test_db_{os.environ.get('FAMILY_AMI_SCHEMA', 'ami_test')}_create"
            
            # Проверяем создание базы данных
            assert schema_manager.create_database(test_db_name) is True
            
            # Пробуем создать ещё раз ту же базу - должно вернуть True, но не вызвать ошибку
            assert schema_manager.create_database(test_db_name) is True
            
            # Проверяем, что база действительно существует, создав подключение
            test_url = (
                f"postgresql://{os.environ.get('FAMILY_ADMIN_USER', 'postgres')}:"
                f"{os.environ.get('FAMILY_ADMIN_PASSWORD', '')}@"
                f"{os.environ.get('FAMILY_DB_HOST', 'localhost')}:"
                f"{os.environ.get('FAMILY_DB_PORT', '5432')}/"
                f"{test_db_name}"
            )
            
            test_engine = create_engine(test_url)
            with test_engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as result")).scalar()
                assert result == 1
        
        finally:
            # Удаляем тестовую базу данных
            admin_user, admin_password = schema_manager._admin_credentials
            postgres_url = (
                f"postgresql://{admin_user}:{admin_password}@"
                f"{schema_manager.config.DB_HOST}:{schema_manager.config.DB_PORT}/postgres"
            )
            try:
                postgres_engine = create_engine(postgres_url)
                with postgres_engine.connect() as conn:
                    conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                    conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            except SQLAlchemyError as e:
                print(f"Ошибка при удалении тестовой базы данных: {e}")

    def test_initialize_ami_memory_with_database_creation(self, schema_manager):
        """
        Проверяет полную инициализацию памяти АМИ, включая создание базы данных.
        
        Этот тест проверяет весь процесс создания памяти АМИ с нуля.
        """
        test_schema = "test_ami_full_init"
        test_db_name = f"test_db_{os.environ.get('FAMILY_AMI_SCHEMA', 'ami_test')}_full"
        
        # Сохраняем оригинальное имя базы данных
        original_db_name = schema_manager.config.DB_NAME
        
        try:
            # Временно меняем имя базы данных для теста
            schema_manager.config.DB_NAME = test_db_name
            
            # Патчим метод execute_sql_script, чтобы не выполнять реальные SQL-скрипты
            with patch.object(schema_manager, 'execute_sql_script', return_value=True):
                # Инициализируем схему с созданием базы
                result = schema_manager.initialize_ami_memory(
                    test_schema,
                    "test_password"
                )
                
                # Проверяем результат
                assert result is True
                
                # Проверяем, что база данных создана, создав подключение
                test_url = (
                    f"postgresql://{os.environ.get('FAMILY_ADMIN_USER', 'postgres')}:"
                    f"{os.environ.get('FAMILY_ADMIN_PASSWORD', '')}@"
                    f"{os.environ.get('FAMILY_DB_HOST', 'localhost')}:"
                    f"{os.environ.get('FAMILY_DB_PORT', '5432')}/"
                    f"{test_db_name}"
                )
                
                test_engine = create_engine(test_url)
                with test_engine.connect() as conn:
                    result = conn.execute(text("SELECT 1 as result")).scalar()
                    assert result == 1
                
                # Проверяем, что схема создана
                assert schema_manager.schema_exists(test_schema) is True
        
        finally:
            # Восстанавливаем оригинальное имя базы данных
            schema_manager.config.DB_NAME = original_db_name
            
            # Удаляем тестовую схему
            schema_manager.drop_schema(test_schema, cascade=True, drop_user=True)
            
            # Удаляем тестовую базу данных
            admin_user, admin_password = schema_manager._admin_credentials
            postgres_url = (
                f"postgresql://{admin_user}:{admin_password}@"
                f"{schema_manager.config.DB_HOST}:{schema_manager.config.DB_PORT}/postgres"
            )
            try:
                postgres_engine = create_engine(postgres_url)
                with postgres_engine.connect() as conn:
                    conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                    # Убеждаемся, что к базе нет активных подключений
                    conn.execute(text(
                        f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        f"WHERE datname = '{test_db_name}' AND pid <> pg_backend_pid()"
                    ))
                    # Удаляем базу
                    conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            except SQLAlchemyError as e:
                print(f"Ошибка при удалении тестовой базы данных: {e}")