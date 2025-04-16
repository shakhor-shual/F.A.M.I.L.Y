"""
Интеграционные тесты для модуля session.py.

Проверяет корректность работы функций для управления сессиями базы данных,
которые являются критическим компонентом подсистемы памяти АМИ,
обеспечивающим сохранение и извлечение воспоминаний.
"""

import logging
import os
import pytest
import dotenv
from pathlib import Path
from sqlalchemy import Column, Integer, String, MetaData, Table, text, inspect
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from undermaind.core.engine import create_db_engine
from undermaind.core.session import (
    create_session_factory, session_scope, create_isolated_session, 
    isolated_session_scope, begin_nested_transaction, refresh_transaction_view,
    ensure_isolated_transactions
)
from undermaind.core.schema_manager import SchemaManager, get_schema_manager
from undermaind.models.base import Base
from undermaind.config import Config

# Настройка логирования для тестов
logger = logging.getLogger(__name__)


# Модель для тестирования, не является тестовым классом
class SessionTestEntity(Base):
    """Тестовая модель для проверки работы сессий."""
    __tablename__ = "session_test_entity"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    
    def __repr__(self):
        return f"<SessionTestEntity(id={self.id}, name='{self.name}')>"


@pytest.fixture(scope="module")
def test_config_path():
    """Путь к файлу конфигурации для тестовой среды."""
    # Ищем в каталоге tests от корня проекта
    base_dir = Path(__file__).resolve().parents[1]
    config_path = base_dir / "test_config.env"
    
    # Если не нашли, ищем в родительском каталоге
    if not config_path.exists():
        config_path = base_dir.parent / "test_config.env"
    
    return config_path


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
        DB_USERNAME=os.environ.get("FAMILY_ADMIN_USER", "family_admin"),
        DB_PASSWORD=os.environ.get("FAMILY_ADMIN_PASSWORD", ""),
        DB_SCHEMA=os.environ.get("FAMILY_DB_SCHEMA", "ami_memory"),
        # Дополнительные параметры для тестов
        DB_POOL_SIZE=2,
        DB_ECHO_SQL=False,
        DB_POOL_RECYCLE=5 # Для теста переиспользования соединений
    )


@pytest.fixture(scope="module")
def admin_credentials():
    """Получает учетные данные администратора PostgreSQL из переменных окружения."""
    # Используем FAMILY_ADMIN_* переменные из test_config.env
    admin_user = os.environ.get("FAMILY_ADMIN_USER")
    admin_password = os.environ.get("FAMILY_ADMIN_PASSWORD")
    
    # Пропускаем тесты, если учетные данные не предоставлены
    if not admin_user or not admin_password:
        pytest.skip("Не указаны учетные данные администратора (FAMILY_ADMIN_USER/FAMILY_ADMIN_PASSWORD) в файле test_config.env. "
                   "Эти данные необходимы для создания тестовой схемы и запуска интеграционных тестов.")
    
    return admin_user, admin_password


@pytest.fixture(scope="module")
def schema_manager(test_config, admin_credentials):
    """Создает экземпляр SchemaManager с установленными учетными данными администратора."""
    admin_user, admin_password = admin_credentials
    manager = SchemaManager(test_config)
    manager.set_admin_credentials(admin_user, admin_password)
    
    # Создаем базу данных, если она не существует
    if not manager.create_database():
        pytest.skip(f"Не удалось создать базу данных {test_config.DB_NAME}")
    
    return manager


@pytest.fixture(scope="module")
def admin_engine(test_config, admin_credentials):
    """Создает движок с правами администратора для управления схемами и таблицами."""
    admin_user, admin_password = admin_credentials
    admin_config = Config(
        DB_NAME=test_config.DB_NAME,
        DB_HOST=test_config.DB_HOST,
        DB_PORT=test_config.DB_PORT,
        DB_USERNAME=admin_user,
        DB_PASSWORD=admin_password,
        DB_SCHEMA="public",
        DB_POOL_SIZE=1,
        DB_ECHO_SQL=False
    )
    return create_db_engine(admin_config, for_admin_tasks=True)


@pytest.fixture(scope="module")
def setup_test_schema(test_config, schema_manager, admin_engine):
    """Создает тестовую схему и таблицу для тестирования сессий."""
    schema_name = "session_test_schema"
    
    try:
        # Если схема существует, удаляем её (для чистоты тестов)
        if schema_manager.schema_exists(schema_name):
            schema_manager.drop_schema(schema_name, cascade=True, drop_user=True)
            
        # Создаем новую схему с правами для тестов
        schema_manager.create_schema(schema_name, "test_password", create_user=True)
        
        # Создаем таблицу для тестов сессий в этой схеме
        with admin_engine.connect() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.session_test_entity (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    description VARCHAR(200)
                )
            """))
            # Предоставляем права обычному пользователю
            conn.execute(text(f"""
                GRANT ALL PRIVILEGES ON {schema_name}.session_test_entity TO {schema_name}
            """))
            # Предоставляем права на последовательность
            conn.execute(text(f"""
                GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema_name} TO {schema_name}
            """))
            conn.commit()
            logger.info(f"Таблица {schema_name}.session_test_entity создана для тестирования сессий")
        
        yield schema_name
        
    finally:
        # Очистка после тестов (гарантируем выполнение)
        schema_manager.drop_schema(schema_name, cascade=True, drop_user=True)
        logger.info(f"Тестовая схема {schema_name} удалена")


@pytest.fixture(scope="module")
def session_engine(test_config, setup_test_schema):
    """Создает движок для тестирования сессий."""
    schema_name = setup_test_schema
    
    # Создаем конфигурацию для подключения к тестовой схеме
    session_config = Config(
        DB_NAME=test_config.DB_NAME,
        DB_HOST=test_config.DB_HOST,
        DB_PORT=test_config.DB_PORT,
        DB_USERNAME=schema_name,  # Используем имя схемы как имя пользователя
        DB_PASSWORD="test_password",
        DB_SCHEMA=schema_name,
        DB_POOL_SIZE=1,
        DB_ECHO_SQL=False
    )
    
    # Создаем движок для обычного пользователя
    engine = create_db_engine(session_config, for_admin_tasks=False)
    
    return engine


@pytest.fixture(scope="module")
def session_factory(session_engine):
    """Создает фабрику сессий для тестирования."""
    return create_session_factory(session_engine)


@pytest.mark.integration
class TestSessionIntegration:
    """
    Интеграционные тесты для функций управления сессиями базы данных.
    
    Проверяет создание сессий, управление транзакциями (commit/rollback),
    и правильное закрытие сессий после работы.
    """
    
    def test_create_session_factory(self, session_engine):
        """
        Проверяет, что функция create_session_factory корректно создает
        фабрику сессий SQLAlchemy.
        """
        # Создаем фабрику сессий
        factory = create_session_factory(session_engine)
        
        # Проверяем, что фабрика создана и имеет ожидаемые методы
        assert factory is not None
        assert hasattr(factory, 'remove')
        assert hasattr(factory, 'query')
        
        # Проверяем, что фабрика привязана к правильному движку
        session = factory()
        assert session.bind == session_engine
        session.close()
    
    def test_session_scope_commit(self, session_factory, setup_test_schema):
        """
        Проверяет успешный коммит изменений при использовании session_scope.
        """
        schema_name = setup_test_schema
        
        # Добавляем запись через контекстный менеджер session_scope
        test_name = "Тестовая запись 1"
        test_description = "Описание тестовой записи для проверки commit"
        
        try:
            # Используем контекстный менеджер для автоматического коммита
            with session_scope(session_factory) as session:
                # Проверяем, что сессия активна
                assert session.is_active
                
                # Вставляем тестовую запись с помощью SQL запроса
                session.execute(
                    text(f"""
                        INSERT INTO {schema_name}.session_test_entity (name, description)
                        VALUES (:name, :description)
                    """),
                    {"name": test_name, "description": test_description}
                )
            
            # Проверяем, что запись действительно сохранена в БД
            with session_scope(session_factory) as session:
                result = session.execute(
                    text(f"""
                        SELECT name, description FROM {schema_name}.session_test_entity
                        WHERE name = :name
                    """),
                    {"name": test_name}
                ).fetchone()
                
                assert result is not None
                assert result[0] == test_name
                assert result[1] == test_description
                
        finally:
            # Очищаем тестовые данные
            with session_scope(session_factory) as session:
                session.execute(
                    text(f"DELETE FROM {schema_name}.session_test_entity WHERE name = :name"),
                    {"name": test_name}
                )
    
    def test_session_scope_rollback(self, session_factory, setup_test_schema):
        """
        Проверяет автоматический откат изменений при исключении внутри session_scope.
        """
        schema_name = setup_test_schema
        
        # Подготавливаем тестовые данные
        test_name = "Тестовая запись для отката"
        
        try:
            # Пытаемся выполнить операцию, которая вызовет исключение 
            # (нарушение ограничения NOT NULL)
            try:
                with session_scope(session_factory) as session:
                    # Сначала вставляем валидную запись
                    session.execute(
                        text(f"""
                            INSERT INTO {schema_name}.session_test_entity (name, description)
                            VALUES (:name, :description)
                        """),
                        {"name": test_name, "description": "Это описание будет откачено"}
                    )
                    
                    # Затем пытаемся вставить невалидную запись (без name)
                    session.execute(
                        text(f"""
                            INSERT INTO {schema_name}.session_test_entity (description)
                            VALUES (:description)
                        """),
                        {"description": "Эта запись вызовет ошибку"}
                    )
                    
                # Если мы дошли до этой точки, значит исключение не было выброшено - это ошибка
                pytest.fail("Ожидалось исключение из-за нарушения ограничения NOT NULL")
                
            except SQLAlchemyError:
                # Это ожидаемое поведение - транзакция должна быть откачена
                pass
            
            # Проверяем, что ни одна из записей не была сохранена в БД из-за отката
            with session_scope(session_factory) as session:
                result = session.execute(
                    text(f"""
                        SELECT COUNT(*) FROM {schema_name}.session_test_entity
                        WHERE name = :name
                    """),
                    {"name": test_name}
                ).scalar()
                
                assert result == 0, "Запись не должна была сохраниться из-за отката транзакции"
                
        finally:
            # Очищаем тестовые данные на всякий случай
            with session_scope(session_factory) as session:
                session.execute(
                    text(f"DELETE FROM {schema_name}.session_test_entity WHERE name = :name"),
                    {"name": test_name}
                )
    
    def test_session_multiple_operations(self, session_factory, setup_test_schema):
        """
        Проверяет выполнение нескольких операций в рамках одной сессии.
        """
        schema_name = setup_test_schema
        
        # Подготавливаем тестовые данные
        test_records = [
            {"name": "Запись 1", "description": "Первая тестовая запись"},
            {"name": "Запись 2", "description": "Вторая тестовая запись"},
            {"name": "Запись 3", "description": "Третья тестовая запись"}
        ]
        
        try:
            # Вставляем несколько записей в одной транзакции
            with session_scope(session_factory) as session:
                for record in test_records:
                    session.execute(
                        text(f"""
                            INSERT INTO {schema_name}.session_test_entity (name, description)
                            VALUES (:name, :description)
                        """),
                        record
                    )
            
            # Проверяем, что все записи сохранены
            with session_scope(session_factory) as session:
                result = session.execute(
                    text(f"""
                        SELECT COUNT(*) FROM {schema_name}.session_test_entity
                        WHERE name IN ('Запись 1', 'Запись 2', 'Запись 3')
                    """)
                ).scalar()
                
                assert result == 3, "Должны быть сохранены все три записи"
                
                # Проверяем каждую запись
                for record in test_records:
                    result = session.execute(
                        text(f"""
                            SELECT description FROM {schema_name}.session_test_entity
                            WHERE name = :name
                        """),
                        {"name": record["name"]}
                    ).scalar()
                    
                    assert result == record["description"]
                
            # Проверяем обновление данных
            with session_scope(session_factory) as session:
                # Обновляем описание для первой записи
                session.execute(
                    text(f"""
                        UPDATE {schema_name}.session_test_entity
                        SET description = :new_description
                        WHERE name = :name
                    """),
                    {"name": "Запись 1", "new_description": "Обновленное описание"}
                )
            
            # Проверяем, что обновление применилось
            with session_scope(session_factory) as session:
                result = session.execute(
                    text(f"""
                        SELECT description FROM {schema_name}.session_test_entity
                        WHERE name = :name
                    """),
                    {"name": "Запись 1"}
                ).scalar()
                
                assert result == "Обновленное описание"
                
        finally:
            # Очищаем тестовые данные
            with session_scope(session_factory) as session:
                session.execute(
                    text(f"""
                        DELETE FROM {schema_name}.session_test_entity
                        WHERE name IN ('Запись 1', 'Запись 2', 'Запись 3')
                    """)
                )
    
    def test_session_independence(self, session_factory, setup_test_schema):
        """
        Проверяет, что разные сессии корректно обмениваются изменениями через механизм транзакций.
        Фокусируется на проверке видимости изменений после commit.
        """
        schema_name = setup_test_schema
        
        # Подготавливаем тестовые данные
        test_name = "Запись для проверки сессий"
        
        try:
            # Создаем две сессии
            session1 = session_factory()
            session2 = session_factory()
            
            try:
                # Шаг 1: Добавляем запись в первой сессии и коммитим
                session1.execute(
                    text(f"""
                        INSERT INTO {schema_name}.session_test_entity (name, description)
                        VALUES (:name, :description)
                    """),
                    {"name": test_name, "description": "Сессия 1"}
                )
                session1.commit()
                
                # Шаг 2: Проверяем, что запись видна во второй сессии после коммита
                result = session2.execute(
                    text(f"""
                        SELECT description FROM {schema_name}.session_test_entity
                        WHERE name = :name
                    """),
                    {"name": test_name}
                ).scalar()
                assert result == "Сессия 1", "Закоммиченные изменения должны быть видны в другой сессии"
                
                # Шаг 3: Обновляем запись во второй сессии и коммитим
                session2.execute(
                    text(f"""
                        UPDATE {schema_name}.session_test_entity
                        SET description = 'Сессия 2'
                        WHERE name = :name
                    """),
                    {"name": test_name}
                )
                session2.commit()
                
                # Шаг 4: Проверяем, что изменения видны в первой сессии после коммита
                # Но сначала обновляем транзакцию, чтобы точно получить актуальные данные
                refresh_transaction_view(session1)
                
                result = session1.execute(
                    text(f"""
                        SELECT description FROM {schema_name}.session_test_entity
                        WHERE name = :name
                    """),
                    {"name": test_name}
                ).scalar()
                assert result == "Сессия 2", "Закоммиченные изменения должны быть видны в первой сессии после обновления транзакции"
                
                # Шаг 5: Демонстрация работы вложенных транзакций
                # Начинаем вложенную транзакцию в первой сессии
                nested = begin_nested_transaction(session1)
                
                # Обновляем запись во вложенной транзакции
                session1.execute(
                    text(f"""
                        UPDATE {schema_name}.session_test_entity
                        SET description = 'Вложенная транзакция'
                        WHERE name = :name
                    """),
                    {"name": test_name}
                )
                
                # Откатываем вложенную транзакцию
                nested.rollback()
                
                # Проверяем, что изменения из вложенной транзакции не сохранились
                result = session1.execute(
                    text(f"""
                        SELECT description FROM {schema_name}.session_test_entity
                        WHERE name = :name
                    """),
                    {"name": test_name}
                ).scalar()
                assert result == "Сессия 2", "Изменения из отмененной вложенной транзакции не должны сохраниться"
                
                # Фиксируем изменения в первой сессии
                session1.commit()
                
            finally:
                session1.close()
                session2.close()
                
        finally:
            # Очищаем тестовые данные
            with session_scope(session_factory) as session:
                session.execute(
                    text(f"DELETE FROM {schema_name}.session_test_entity WHERE name = :name"),
                    {"name": test_name}
                )
    
    def test_concurrent_sessions(self, session_factory, setup_test_schema):
        """
        Проверяет работу нескольких параллельных сессий с одной базой данных.
        Имитирует сценарий, когда несколько компонентов системы одновременно
        обращаются к памяти АМИ.
        """
        schema_name = setup_test_schema
        
        # Уникальные идентификаторы для тестовых записей
        test_prefixes = ["Компонент A", "Компонент B", "Компонент C"]
        
        try:
            # Имитируем работу трех компонентов системы в отдельных сессиях
            for i, prefix in enumerate(test_prefixes):
                with session_scope(session_factory) as session:
                    # Каждый компонент создает свою запись
                    session.execute(
                        text(f"""
                            INSERT INTO {schema_name}.session_test_entity (name, description)
                            VALUES (:name, :description)
                        """),
                        {
                            "name": f"{prefix} - Запись",
                            "description": f"Запись создана компонентом {prefix}"
                        }
                    )
            
            # Проверяем, что все записи сохранены
            with session_scope(session_factory) as session:
                for prefix in test_prefixes:
                    result = session.execute(
                        text(f"""
                            SELECT description FROM {schema_name}.session_test_entity
                            WHERE name = :name
                        """),
                        {"name": f"{prefix} - Запись"}
                    ).scalar()
                    
                    assert result is not None
                    assert f"компонентом {prefix}" in result
                
                # Проверяем общее количество записей
                result = session.execute(
                    text(f"""
                        SELECT COUNT(*) FROM {schema_name}.session_test_entity
                        WHERE name LIKE '%Компонент%'
                    """)
                ).scalar()
                
                assert result == len(test_prefixes)
                
        finally:
            # Очищаем тестовые данные
            with session_scope(session_factory) as session:
                session.execute(
                    text(f"""
                        DELETE FROM {schema_name}.session_test_entity
                        WHERE name LIKE '%Компонент%'
                    """)
                )
    
    def test_isolated_session_scope(self, session_factory, setup_test_schema):
        """
        Проверяет контекстный менеджер isolated_session_scope для работы с изолированными сессиями.
        """
        from undermaind.core.session import isolated_session_scope
        
        schema_name = setup_test_schema
        test_name = "Тест изолированной сессии"
        
        try:
            # Вставляем данные в изолированной сессии с высоким уровнем изоляции
            with isolated_session_scope(session_factory, "SERIALIZABLE") as session:
                session.execute(
                    text(f"""
                        INSERT INTO {schema_name}.session_test_entity (name, description)
                        VALUES (:name, :description)
                    """),
                    {"name": test_name, "description": "Изолированная сессия"}
                )
            
            # Проверяем, что данные сохранены
            with session_scope(session_factory) as session:
                result = session.execute(
                    text(f"""
                        SELECT description FROM {schema_name}.session_test_entity
                        WHERE name = :name
                    """),
                    {"name": test_name}
                ).scalar()
                
                assert result == "Изолированная сессия"
                
        finally:
            # Очищаем тестовые данные
            with session_scope(session_factory) as session:
                session.execute(
                    text(f"DELETE FROM {schema_name}.session_test_entity WHERE name = :name"),
                    {"name": test_name}
                )
    
    def test_nested_transaction(self, session_factory, setup_test_schema):
        """
        Проверяет работу вложенных транзакций.
        """
        from undermaind.core.session import begin_nested_transaction
        
        schema_name = setup_test_schema
        test_name_outer = "Внешняя транзакция"
        test_name_nested = "Вложенная транзакция"
        
        try:
            # Создаем сессию для тестирования вложенных транзакций
            session = session_factory()
            
            try:
                # Начинаем внешнюю транзакцию
                session.begin()
                
                # Вставляем первую запись во внешней транзакции
                session.execute(
                    text(f"""
                        INSERT INTO {schema_name}.session_test_entity (name, description)
                        VALUES (:name, :description)
                    """),
                    {"name": test_name_outer, "description": "Запись из внешней транзакции"}
                )
                
                # Начинаем вложенную транзакцию (SAVEPOINT)
                nested = begin_nested_transaction(session)
                
                # Вставляем запись во вложенной транзакции
                session.execute(
                    text(f"""
                        INSERT INTO {schema_name}.session_test_entity (name, description)
                        VALUES (:name, :description)
                    """),
                    {"name": test_name_nested, "description": "Запись из вложенной транзакции"}
                )
                
                # Откатываем вложенную транзакцию
                nested.rollback()
                
                # Проверяем, что запись из вложенной транзакции не сохранилась
                result = session.execute(
                    text(f"""
                        SELECT COUNT(*) FROM {schema_name}.session_test_entity
                        WHERE name = :name
                    """),
                    {"name": test_name_nested}
                ).scalar()
                
                assert result == 0, "Запись из вложенной транзакции не должна сохраниться после отката"
                
                # Проверяем, что запись из внешней транзакции все еще существует
                result = session.execute(
                    text(f"""
                        SELECT description FROM {schema_name}.session_test_entity
                        WHERE name = :name
                    """),
                    {"name": test_name_outer}
                ).scalar()
                
                assert result == "Запись из внешней транзакции", "Запись из внешней транзакции должна сохраниться"
                
                # Коммитим внешнюю транзакцию
                session.commit()
                
                # Проверяем, что запись из внешней транзакции сохранилась в базе
                session2 = session_factory()
                try:
                    result = session2.execute(
                        text(f"""
                            SELECT COUNT(*) FROM {schema_name}.session_test_entity
                            WHERE name = :name
                        """),
                        {"name": test_name_outer}
                    ).scalar()
                    
                    assert result == 1, "Запись из внешней транзакции должна сохраниться после коммита"
                    
                    # Проверяем, что запись из вложенной транзакции не сохранилась
                    result = session2.execute(
                        text(f"""
                            SELECT COUNT(*) FROM {schema_name}.session_test_entity
                            WHERE name = :name
                        """),
                        {"name": test_name_nested}
                    ).scalar()
                    
                    assert result == 0, "Запись из вложенной транзакции не должна сохраниться после отката"
                finally:
                    session2.close()
                
            finally:
                session.close()
                
        finally:
            # Очищаем тестовые данные
            with session_scope(session_factory) as session:
                session.execute(
                    text(f"""
                        DELETE FROM {schema_name}.session_test_entity 
                        WHERE name IN (:name1, :name2)
                    """),
                    {"name1": test_name_outer, "name2": test_name_nested}
                )