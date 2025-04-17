"""
Интеграционные тесты для AmiInitializer.

Проверяет функциональность инициализации АМИ (Artificial Mind Identity) в базе данных F.A.M.I.L.Y.,
что является ключевым компонентом для обеспечения идентичности и памяти искусственного разума.
"""

import os
import pytest
import logging
import dotenv
from pathlib import Path
import psycopg2

from undermaind.utils.ami_init import AmiInitializer
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
def test_ami_name():
    """Имя тестового АМИ"""
    return "ami_test_user"


@pytest.fixture(scope="module")
def test_ami_schema():
    """Имя схемы тестового АМИ"""
    return "ami_test_user"  # Обновлено: имя схемы теперь равно имени АМИ, без дополнительного префикса


@pytest.fixture(scope="module")
def test_ami_password():
    """Пароль тестового АМИ"""
    return "ami_secure_password"


@pytest.fixture(scope="module")
def db_initializer(test_config_path):
    """Создает экземпляр DatabaseInitializer для тестов."""
    # Загружаем конфигурацию из тестового файла
    dotenv.load_dotenv(test_config_path)
    
    db_init = DatabaseInitializer(
        db_host=os.environ.get("FAMILY_DB_HOST", "localhost"),
        db_port=int(os.environ.get("FAMILY_DB_PORT", "5432")),
        db_name=os.environ.get("FAMILY_DB_NAME", "family_db"),
        admin_user=os.environ.get("FAMILY_ADMIN_USER", "family_admin"),
        admin_password=os.environ.get("FAMILY_ADMIN_PASSWORD"),
    )
    
    # Убеждаемся, что база данных инициализирована
    if not db_init.database_exists():
        db_init.initialize_database()
    
    return db_init


@pytest.fixture(scope="module")
def ami_initializer(test_config_path, test_ami_name, test_ami_password):
    """Создает экземпляр AmiInitializer для тестов."""
    # Загружаем конфигурацию из тестового файла
    dotenv.load_dotenv(test_config_path)
    
    return AmiInitializer(
        ami_name=test_ami_name,
        ami_password=test_ami_password,
        db_host=os.environ.get("FAMILY_DB_HOST", "localhost"),
        db_port=int(os.environ.get("FAMILY_DB_PORT", "5432")),
        db_name=os.environ.get("FAMILY_DB_NAME", "family_db"),
        admin_user=os.environ.get("FAMILY_ADMIN_USER", "family_admin"),
        admin_password=os.environ.get("FAMILY_ADMIN_PASSWORD"),
    )


@pytest.mark.integration
class TestAmiInitializerIntegration:
    """
    Интеграционные тесты для AmiInitializer.
    
    Проверяет создание, удаление и пересоздание пользователя АМИ и его схемы
    в реальном окружении PostgreSQL.
    """
    
    def test_ami_not_exists_initially(self, ami_initializer, test_ami_name):
        """Проверяет, что АМИ изначально не существует."""
        # Удаляем АМИ, если он уже существует
        if ami_initializer.ami_exists():
            ami_initializer.drop_ami(force=True)
        
        # Проверяем, что АМИ не существует
        assert ami_initializer.ami_exists() is False
        
        # Проверяем через прямое подключение
        with ami_initializer._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s",
                    (test_ami_name,)
                )
                assert cur.fetchone() is None

    def test_create_ami(self, ami_initializer, test_ami_name, test_ami_schema):
        """Проверяет создание АМИ."""
        # Удаляем АМИ, если он уже существует
        if ami_initializer.ami_exists():
            ami_initializer.drop_ami(force=True)
        
        # Создаем АМИ
        assert ami_initializer.create_ami() is True
        
        # Проверяем, что АМИ существует
        assert ami_initializer.ami_exists() is True
        
        # Проверяем через прямое подключение, что пользователь АМИ создан
        with ami_initializer._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s",
                    (test_ami_name,)
                )
                assert cur.fetchone() is not None
                
                # Проверяем, что схема АМИ создана (с префиксом ami_)
                cur.execute(
                    "SELECT 1 FROM pg_namespace WHERE nspname = %s",
                    (test_ami_schema,)
                )
                assert cur.fetchone() is not None
                
                # Проверяем, что основные таблицы созданы в схеме АМИ
                cur.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = '{test_ami_schema}'
                """)
                table_count = cur.fetchone()[0]
                assert table_count > 0, "В схеме АМИ должны быть созданы таблицы"

    def test_drop_ami(self, ami_initializer, test_ami_name, test_ami_schema):
        """Проверяет удаление АМИ."""
        # Создаем АМИ, если он не существует
        if not ami_initializer.ami_exists():
            ami_initializer.create_ami()
        
        # Удаляем АМИ
        assert ami_initializer.drop_ami(force=True) is True
        
        # Проверяем, что АМИ не существует
        assert ami_initializer.ami_exists() is False
        
        # Проверяем через прямое подключение, что пользователь АМИ удален
        with ami_initializer._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s",
                    (test_ami_name,)
                )
                assert cur.fetchone() is None
                
                # Проверяем, что схема АМИ удалена
                cur.execute(
                    "SELECT 1 FROM pg_namespace WHERE nspname = %s",
                    (test_ami_schema,)
                )
                assert cur.fetchone() is None

    def test_recreate_ami(self, ami_initializer, test_ami_name, test_ami_schema):
        """Проверяет пересоздание АМИ."""
        # Создаем АМИ, если он не существует
        if not ami_initializer.ami_exists():
            ami_initializer.create_ami()
        
        # Заполняем таблицу experiences тестовыми данными
        with ami_initializer._get_db_connection() as conn:
            with conn.cursor() as cur:
                try:
                    # Проверяем существование таблицы experiences в схеме АМИ
                    cur.execute(f"""
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = '{test_ami_schema}' 
                        AND table_name = 'experiences'
                    """)
                    if cur.fetchone():
                        # Вставляем тестовую запись
                        cur.execute(f"""
                            INSERT INTO {test_ami_schema}.experiences 
                            (information_category, experience_type, subjective_position, content) 
                            VALUES ('self', 'thought', 'reflective', 'Тестовый опыт для проверки пересоздания АМИ')
                        """)
                        conn.commit()
                except Exception as e:
                    logger.error(f"Ошибка при заполнении тестовыми данными: {e}")
                    conn.rollback()
        
        # Пересоздаем АМИ
        assert ami_initializer.recreate_ami(force=True) is True
        
        # Проверяем, что АМИ существует
        assert ami_initializer.ami_exists() is True
        
        # Проверяем, что таблица experiences пуста (пересоздана)
        with ami_initializer._get_db_connection() as conn:
            with conn.cursor() as cur:
                # Проверяем существование таблицы experiences в схеме АМИ
                cur.execute(f"""
                    SELECT COUNT(*) FROM {test_ami_schema}.experiences
                """)
                count = cur.fetchone()[0]
                assert count == 0, "Таблица experiences должна быть пуста после пересоздания АМИ"

    def test_connection_as_ami(self, ami_initializer, test_ami_name, test_ami_password, test_ami_schema):
        """Проверяет возможность подключения с учетными данными АМИ."""
        # Создаем АМИ, если он не существует
        if not ami_initializer.ami_exists():
            ami_initializer.create_ami()
        
        # Пробуем подключиться с учетными данными АМИ
        try:
            conn = psycopg2.connect(
                host=ami_initializer.db_init.db_host,
                port=ami_initializer.db_init.db_port,
                database=ami_initializer.db_init.db_name,
                user=test_ami_name,
                password=test_ami_password,
                application_name=f"ami_{test_ami_name}_test"
            )
            
            # Проверяем, что подключение работает
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                assert cur.fetchone() is not None
                
                # Проверяем доступ к схеме АМИ (с префиксом ami_)
                cur.execute(f"SET search_path TO {test_ami_schema}")
                
                # Проверяем доступ к таблицам в схеме АМИ
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()")
                tables = [row[0] for row in cur.fetchall()]
                
                assert len(tables) > 0, "АМИ должен иметь доступ к таблицам в своей схеме"
            
            conn.close()
            connection_successful = True
        except Exception as e:
            logger.error(f"Ошибка при подключении с учетными данными АМИ: {e}")
            connection_successful = False
        
        assert connection_successful, "Подключение с учетными данными АМИ должно быть успешным"