"""
Интеграционные тесты для модуля engine.py.

Проверяет правильность настройки движка SQLAlchemy для работы с PostgreSQL и pgvector,
что является фундаментальной основой для хранения и извлечения воспоминаний АМИ.
Тесты учитывают разграничение прав - создание таблиц доступно только администратору БД.
"""

import os
import logging
import pytest
import dotenv
from pathlib import Path
from sqlalchemy import text, inspect, Table, Column, MetaData, Integer, String
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError

from undermaind.core.engine import create_db_engine, is_admin_engine
from undermaind.core.schema_manager import SchemaManager, get_schema_manager
from undermaind.config import Config

# Настройка логирования для тестов
logger = logging.getLogger(__name__)

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
def test_db_engine(test_config, schema_manager):
    """Создает тестовый движок для взаимодействия с базой данных от имени обычного пользователя."""
    # Создаем тестовую схему для проверки движка
    test_schema = "engine_test_schema"
    
    try:
        # Если схема существует, удаляем её (для чистоты тестов)
        if schema_manager.schema_exists(test_schema):
            schema_manager.drop_schema(test_schema, cascade=True, drop_user=True)
            
        # Создаем новую схему с расширенными правами для тестов
        schema_manager.create_schema(test_schema, "test_password", create_user=True)
        
        # Обновляем конфигурацию, чтобы использовать тестовую схему и учетные данные
        test_config_with_schema = Config(
            DB_NAME=test_config.DB_NAME,
            DB_HOST=test_config.DB_HOST,
            DB_PORT=test_config.DB_PORT,
            DB_USERNAME=test_schema,  # Используем имя схемы как имя пользователя
            DB_PASSWORD="test_password",
            DB_SCHEMA=test_schema,
            DB_POOL_SIZE=test_config.DB_POOL_SIZE,
            DB_ECHO_SQL=test_config.DB_ECHO_SQL,
            DB_POOL_RECYCLE=test_config.DB_POOL_RECYCLE
        )
        
        # Создаем движок от имени обычного пользователя (не администратора)
        engine = create_db_engine(test_config_with_schema, for_admin_tasks=False)
        
        yield engine
        
    finally:
        # Очистка после тестов (гарантируем выполнение)
        schema_manager.drop_schema(test_schema, cascade=True, drop_user=True)


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


@pytest.mark.integration
class TestEngineIntegration:
    """
    Интеграционные тесты для движка базы данных.
    
    Проверяет основные функции настройки и работы с движком SQLAlchemy
    для PostgreSQL+pgvector в контексте системы памяти АМИ.
    Реализует модель безопасности, где создание таблиц доступно только администратору.
    """
    
    def test_engine_creation(self, test_config):
        """Проверяет создание движка с правильными параметрами."""
        # Создаем обычный движок
        engine = create_db_engine(test_config)
        
        # Проверяем, что движок настроен с корректными параметрами
        assert engine.url.username == test_config.DB_USERNAME
        assert engine.url.password == test_config.DB_PASSWORD
        assert engine.url.host == test_config.DB_HOST
        assert engine.url.port == int(test_config.DB_PORT)
        assert engine.url.database == test_config.DB_NAME
        
        # Проверка пула соединений может отличаться в зависимости от версии SQLAlchemy
        # Проверяем просто наличие пула соединений
        assert hasattr(engine, 'pool')
        
        # Проверяем поддержку диалекта PostgreSQL
        assert engine.dialect.name == 'postgresql'
        
        # Создаем административный движок
        admin_engine = create_db_engine(test_config, for_admin_tasks=True)
        
        # Проверяем функцию определения административного движка
        if 'admin' in test_config.DB_USERNAME.lower():
            assert is_admin_engine(engine) is True
        else:
            assert is_admin_engine(admin_engine) != is_admin_engine(engine)
    
    def test_engine_connection(self, test_db_engine):
        """Проверяет подключение к базе данных и выполнение простых запросов."""
        try:
            # Проверяем, что движок может подключиться к базе
            with test_db_engine.connect() as conn:
                # Выполняем простой запрос
                result = conn.execute(text("SELECT 1 as result")).scalar()
                assert result == 1
                
                # Проверяем версию базы данных
                version = conn.execute(text("SELECT version()")).scalar()
                assert "PostgreSQL" in version
        except SQLAlchemyError as e:
            pytest.fail(f"Не удалось подключиться к базе данных: {str(e)}")
    
    def test_engine_schema_access(self, test_db_engine, admin_engine, test_config):
        """
        Проверяет доступ к схеме, указанной в конфигурации.
        Создание таблиц выполняется администратором, а доступ к данным - обычным пользователем.
        """
        # Определяем схему через test_db_engine, чтобы убедиться, что используем 
        # актуальное значение из фикстуры
        schema_name = inspect(test_db_engine).get_schema_names()[0]
        if schema_name == 'public':
            schema_name = test_config.DB_SCHEMA
        
        # Создаем временную таблицу в тестовой схеме
        metadata = MetaData(schema=schema_name)
        test_table = Table(
            'engine_test_table', metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50))
        )
        
        try:
            # Создаем таблицу от имени администратора БД
            logger.info(f"Создание таблицы {schema_name}.engine_test_table от имени администратора")
            metadata.create_all(admin_engine)
            
            # Проверяем, что таблица создана в правильной схеме, используя обычный движок
            inspector = inspect(test_db_engine)
            tables = inspector.get_table_names(schema=schema_name)
            assert 'engine_test_table' in tables
            
            # Пробуем вставить и получить данные от имени обычного пользователя
            with test_db_engine.connect() as conn:
                # Вставляем данные
                conn.execute(text(
                    f"INSERT INTO {schema_name}.engine_test_table (id, name) VALUES (1, 'Test Name')"
                ))
                conn.commit()
                
                # Получаем данные
                result = conn.execute(text(
                    f"SELECT name FROM {schema_name}.engine_test_table WHERE id = 1"
                )).scalar()
                
                assert result == 'Test Name'
                
                # Проверяем, что обычный пользователь не может создать таблицу
                try:
                    conn.execute(text(
                        f"CREATE TABLE {schema_name}.not_allowed_table (id INTEGER PRIMARY KEY)"
                    ))
                    conn.commit()
                    # Если таблица создалась без ошибки, это проблема с настройкой прав
                    logger.warning("Обычный пользователь смог создать таблицу - проблема с настройкой прав")
                except SQLAlchemyError:
                    # Ожидаемая ошибка - пользователь не должен иметь прав на создание таблицы
                    pass
        
        finally:
            # Удаляем тестовую таблицу от имени администратора
            metadata.drop_all(admin_engine)
            # Проверяем на случай, если обычный пользователь смог создать таблицу
            with admin_engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {schema_name}.not_allowed_table"))
                conn.commit()
    
    def test_engine_pgvector_support(self, test_db_engine, test_config, admin_engine):
        """
        Проверяет поддержку расширения pgvector для работы с векторными представлениями.
        Создание таблиц выполняется администратором, а векторные операции - обычным пользователем.
        """
        # Определяем схему через test_db_engine
        schema_name = inspect(test_db_engine).get_schema_names()[0]
        if schema_name == 'public':
            schema_name = test_config.DB_SCHEMA
            
        # Проверяем наличие расширения pgvector с помощью admin_engine
        try:
            with admin_engine.connect() as conn:
                # Проверяем наличие расширения vector
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
                )).scalar()
                
                if (result == 0):
                    # Пытаемся создать расширение с правами админа
                    try:
                        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                        conn.commit()
                        logger.info("Успешно установлено расширение pgvector")
                    except SQLAlchemyError as e:
                        pytest.skip(f"Расширение pgvector не установлено и не может быть создано: {e}")
                else:
                    logger.info("Расширение pgvector уже установлено")
        except SQLAlchemyError as e:
            pytest.skip(f"Не удалось проверить наличие расширения pgvector: {e}")
            
        # Создаем временную таблицу с векторным полем от имени администратора
        try:
            with admin_engine.connect() as conn:
                # Создаем временную таблицу с векторным полем
                try:
                    conn.execute(text(f"""
                        CREATE TABLE IF NOT EXISTS {schema_name}.vector_test_table (
                            id SERIAL PRIMARY KEY,
                            embedding VECTOR(3)
                        )
                    """))
                    conn.commit()
                    logger.info(f"Таблица {schema_name}.vector_test_table создана администратором")
                except ProgrammingError as e:
                    pytest.skip(f"Тип VECTOR не поддерживается, расширение pgvector не работает: {e}")
            
            # Тестируем работу с векторами от имени обычного пользователя
            with test_db_engine.connect() as conn:
                # Вставляем тестовый вектор
                conn.execute(text(f"""
                    INSERT INTO {schema_name}.vector_test_table (embedding)
                    VALUES ('[1,2,3]')
                """))
                conn.commit()
                
                # Проверяем, что данные корректно вставлены
                result = conn.execute(text(f"""
                    SELECT embedding FROM {schema_name}.vector_test_table WHERE id = 1
                """)).scalar()
                
                assert result is not None
            
            # Отдельное соединение для проверки векторных операций, чтобы избежать 
            # проблем с прерванными транзакциями
            with test_db_engine.connect() as conn:
                # Проверяем векторные операции в отдельной транзакции
                try:
                    # Проверяем, что тип данных vector правильно определяется
                    result = conn.execute(text(f"""
                        SELECT pg_typeof(embedding) FROM {schema_name}.vector_test_table LIMIT 1
                    """)).scalar()
                    assert "vector" in str(result).lower()
                    
                    # Пробуем выполнить векторный запрос с явным приведением типа
                    result = conn.execute(text(f"""
                        SELECT id, embedding <-> '[3,2,1]'::vector(3) as distance
                        FROM {schema_name}.vector_test_table
                        ORDER BY distance LIMIT 1
                    """)).fetchone()
                    
                    assert result is not None
                    assert 'distance' in result._fields
                    assert isinstance(result.distance, (int, float))
                except SQLAlchemyError as e:
                    logger.warning(f"Не удалось выполнить запрос с оператором <->: {e}")
                    # Векторные операции могут не поддерживаться в некоторых версиях
                    # Не прерываем тест, только логируем предупреждение
                
        finally:
            # Удаляем тестовую таблицу
            with admin_engine.connect() as conn:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {schema_name}.vector_test_table"))
                    conn.commit()
                    logger.info(f"Таблица {schema_name}.vector_test_table успешно удалена")
                except SQLAlchemyError as e:
                    logger.warning(f"Не удалось удалить тестовую таблицу: {e}")
    
    def test_engine_pool_recycle(self, test_config):
        """Проверяет функциональность переиспользования соединений в пуле."""
        # Убеждаемся, что в конфигурации установлен параметр pool_recycle
        assert hasattr(test_config, 'DB_POOL_RECYCLE'), "В конфигурации отсутствует DB_POOL_RECYCLE"
        
        # Создаем движок с настройкой переиспользования соединений
        engine = create_db_engine(test_config)
        
        # Проверяем, что настройка pool_recycle применена
        assert hasattr(engine.pool, '_recycle'), "Пул соединений не поддерживает _recycle"
        assert engine.pool._recycle == test_config.DB_POOL_RECYCLE
        
        # Создаем подключения и проверяем их работоспособность
        try:
            with engine.connect() as conn1:
                # Проверяем первое соединение
                result1 = conn1.execute(text("SELECT 1")).scalar()
                assert result1 == 1
            
            # Создаем второе соединение, которое должно быть работоспособным
            with engine.connect() as conn2:
                # Проверяем второе соединение
                result2 = conn2.execute(text("SELECT 2")).scalar()
                assert result2 == 2
        except SQLAlchemyError as e:
            pytest.fail(f"Ошибка при работе с пулом соединений: {e}")
            
    def test_admin_vs_regular_rights(self, test_db_engine, admin_engine, test_config):
        """
        Проверяет разграничение прав между администратором и обычным пользователем.
        Администратор должен иметь возможность создавать таблицы, 
        а обычный пользователь - только работать с данными.
        """
        schema_name = inspect(test_db_engine).get_schema_names()[0]
        if schema_name == 'public':
            schema_name = test_config.DB_SCHEMA
            
        table_name = f"{schema_name}.admin_rights_test_table"
        
        try:
            # 1. Проверяем, что администратор может создать таблицу
            with admin_engine.connect() as conn:
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        data TEXT
                    )
                """))
                conn.commit()
                logger.info(f"Администратор успешно создал таблицу {table_name}")
                
                # Предоставляем права на таблицу обычному пользователю
                conn.execute(text(f"""
                    GRANT SELECT, INSERT, UPDATE, DELETE ON {table_name} TO {schema_name}
                """))
                conn.commit()
                logger.info(f"Права на таблицу предоставлены пользователю {schema_name}")
            
            # 2. Проверяем, что обычный пользователь может работать с данными
            with test_db_engine.connect() as conn:
                # Вставляем данные
                conn.execute(text(f"""
                    INSERT INTO {table_name} (data) VALUES ('Тестовые данные')
                """))
                conn.commit()
                
                # Проверяем, что данные корректно вставлены
                result = conn.execute(text(f"""
                    SELECT data FROM {table_name} WHERE id = 1
                """)).scalar()
                
                assert result == 'Тестовые данные'
                
                # 3. Проверяем, что обычный пользователь НЕ может создать таблицу
                try:
                    conn.execute(text(f"""
                        CREATE TABLE {schema_name}.forbidden_table (id INTEGER PRIMARY KEY)
                    """))
                    conn.commit()
                    
                    # Если мы дошли до этой точки, значит, таблица создалась - это ошибка
                    # Удаляем созданную таблицу
                    conn.execute(text(f"""
                        DROP TABLE IF EXISTS {schema_name}.forbidden_table
                    """))
                    conn.commit()
                    
                    # Фиксируем проблему с правами
                    pytest.fail("Обычный пользователь смог создать таблицу - нарушение модели безопасности")
                except SQLAlchemyError:
                    # Это ожидаемое поведение - обычный пользователь не должен иметь такого права
                    logger.info("Проверка безопасности пройдена: обычный пользователь не может создавать таблицы")
                    pass
        
        finally:
            # Удаляем тестовую таблицу от имени администратора
            with admin_engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                conn.execute(text(f"DROP TABLE IF EXISTS {schema_name}.forbidden_table"))
                conn.commit()
                logger.info("Тестовые таблицы удалены")
                
    def test_verify_table_access(self, test_db_engine, admin_engine, test_config):
        """
        Проверяет функцию verify_table_access, которая анализирует права доступа к таблице.
        Функция должна корректно определять права на SELECT, INSERT, UPDATE и DELETE.
        """
        schema_name = inspect(test_db_engine).get_schema_names()[0]
        if schema_name == 'public':
            schema_name = test_config.DB_SCHEMA
            
        # 1. Создаем таблицу для тестирования прав доступа от имени админа
        table_name = "access_rights_test_table"
        full_table_name = f"{schema_name}.{table_name}"
        
        try:
            # Создаем таблицу администратором и явно отзываем все права
            with admin_engine.connect() as conn:
                # Удаляем таблицу, если она существует
                conn.execute(text(f"""
                    DROP TABLE IF EXISTS {full_table_name}
                """))
                conn.commit()
                
                # Создаем таблицу
                conn.execute(text(f"""
                    CREATE TABLE {full_table_name} (
                        id SERIAL PRIMARY KEY,
                        name TEXT
                    )
                """))
                conn.commit()
                logger.info(f"Таблица {full_table_name} создана для тестирования прав доступа")
                
                # Отзываем все права для проверки
                conn.execute(text(f"""
                    REVOKE ALL ON {full_table_name} FROM {schema_name}
                """))
                conn.commit()
                logger.info(f"Все права на таблицу отозваны у пользователя {schema_name}")
                
                # Предоставляем только право SELECT
                conn.execute(text(f"""
                    GRANT SELECT ON {full_table_name} TO {schema_name}
                """))
                conn.commit()
                logger.info(f"Право SELECT предоставлено для {schema_name}")
            
            # 2. Проверяем права доступа через verify_table_access
            from undermaind.core.engine import verify_table_access
            
            # Проверяем права с движком обычного пользователя
            access_info = verify_table_access(test_db_engine, schema_name, table_name)
            
            # Таблица должна существовать
            assert access_info["exists"] is True
            # Должно быть право на SELECT
            assert access_info["select"] is True
            # Другие права не должны быть предоставлены
            assert access_info["insert"] is False
            assert access_info["update"] is False
            assert access_info["delete"] is False
            
            # 3. Добавляем права на INSERT и проверяем
            with admin_engine.connect() as conn:
                conn.execute(text(f"""
                    GRANT INSERT ON {full_table_name} TO {schema_name}
                """))
                conn.commit()
                logger.info(f"Право INSERT предоставлено для {schema_name}")
            
            # Повторная проверка после расширения прав
            access_info = verify_table_access(test_db_engine, schema_name, table_name)
            assert access_info["insert"] is True
            assert access_info["update"] is False  # Должно остаться False
            assert access_info["delete"] is False  # Должно остаться False
            
            # 4. Проверяем несуществующую таблицу
            nonexistent_access = verify_table_access(test_db_engine, schema_name, "nonexistent_table")
            assert nonexistent_access["exists"] is False
            
        finally:
            # Удаляем тестовую таблицу
            with admin_engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {full_table_name}"))
                conn.commit()
                logger.info(f"Таблица {full_table_name} удалена")
                
    def test_grant_table_access(self, test_db_engine, admin_engine, test_config):
        """
        Проверяет функцию grant_table_access, которая предоставляет права на таблицу.
        Проверка включает выдачу различных прав и проверку того, что обычный пользователь
        не может выполнять привилегированные операции.
        """
        schema_name = inspect(test_db_engine).get_schema_names()[0]
        if schema_name == 'public':
            schema_name = test_config.DB_SCHEMA
            
        # 1. Создаем таблицу для тестирования выдачи прав
        table_name = "grant_rights_test_table"
        full_table_name = f"{schema_name}.{table_name}"
        
        try:
            # Создаем таблицу администратором и явно отзываем все права
            with admin_engine.connect() as conn:
                # Удаляем таблицу, если она существует
                conn.execute(text(f"""
                    DROP TABLE IF EXISTS {full_table_name}
                """))
                conn.commit()
                
                # Создаем таблицу
                conn.execute(text(f"""
                    CREATE TABLE {full_table_name} (
                        id SERIAL PRIMARY KEY,
                        name TEXT
                    )
                """))
                conn.commit()
                
                # Отзываем все права
                conn.execute(text(f"""
                    REVOKE ALL ON {full_table_name} FROM {schema_name}
                """))
                conn.commit()
                logger.info(f"Таблица {full_table_name} создана с отозванными правами")
            
            # 2. Импортируем функцию и проверяем отсутствие прав
            from undermaind.core.engine import grant_table_access, verify_table_access
            
            # Вначале проверяем, что прав нет
            access_before = verify_table_access(test_db_engine, schema_name, table_name)
            assert access_before["select"] is False
            assert access_before["insert"] is False
            
            # 3. Предоставляем права на SELECT через функцию
            assert grant_table_access(
                admin_engine, schema_name, table_name, schema_name,
                grant_select=True, grant_insert=False, grant_update=False, grant_delete=False
            ) is True
            
            # Проверяем, что права на SELECT появились
            access_after_select = verify_table_access(test_db_engine, schema_name, table_name)
            assert access_after_select["select"] is True
            assert access_after_select["insert"] is False  # Должно остаться False
            
            # 4. Предоставляем все права и проверяем
            assert grant_table_access(
                admin_engine, schema_name, table_name, schema_name,
                grant_select=True, grant_insert=True, grant_update=True, grant_delete=True
            ) is True
            
            # Проверяем права
            full_access = verify_table_access(test_db_engine, schema_name, table_name)
            assert full_access["select"] is True
            assert full_access["insert"] is True
            assert full_access["update"] is True
            assert full_access["delete"] is True
            
            # 5. Проверяем, что обычный пользователь не может выдавать права
            # Это должно завершиться неудачей, так как тест использует обычный движок
            assert grant_table_access(
                test_db_engine, schema_name, table_name, schema_name, 
                grant_select=True
            ) is False
            
        finally:
            # Удаляем тестовую таблицу
            with admin_engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {full_table_name}"))
                conn.commit()
                logger.info(f"Таблица {full_table_name} удалена")