"""
Настройка и создание SQLAlchemy engine.

Модуль предоставляет функции для создания и настройки движка SQLAlchemy
для работы с PostgreSQL и расширением pgvector, с учетом разделения прав
между администраторами (создание таблиц) и обычными пользователями (чтение/запись).
"""

import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import SQLAlchemyError
from ..config import Config

# Настройка логирования
logger = logging.getLogger(__name__)


def create_db_engine(config: Config, for_admin_tasks=False):
    """
    Создает и настраивает движок SQLAlchemy для работы с PostgreSQL+pgvector.
    
    Args:
        config (Config): Объект конфигурации с параметрами подключения
        for_admin_tasks (bool, optional): Если True, движок создается для административных
                                        задач (создание схем, таблиц). По умолчанию False.
        
    Returns:
        Engine: SQLAlchemy Engine
    """
    connection_url = URL.create(
        drivername='postgresql+psycopg2',
        username=config.DB_USERNAME,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME
    )
    
    # Создаем явные параметры для пула соединений
    engine_kwargs = {
        'pool_pre_ping': True,
        'echo': config.DB_ECHO_SQL
    }
    
    # Добавляем параметры пула, только если они определены в конфигурации
    if hasattr(config, 'DB_POOL_SIZE') and isinstance(config.DB_POOL_SIZE, (int)):
        engine_kwargs['pool_size'] = max(1, config.DB_POOL_SIZE)  # Минимум 1 соединение
    
    if hasattr(config, 'DB_POOL_RECYCLE') and isinstance(config.DB_POOL_RECYCLE, (int)):
        engine_kwargs['pool_recycle'] = config.DB_POOL_RECYCLE
    
    # Формируем опции для создания соединения в зависимости от типа пользователя
    if for_admin_tasks:
        # Для админских задач устанавливаем отдельный пул, чтобы избежать
        # конфликтов с обычными соединениями
        if 'pool_size' in engine_kwargs:
            # Для админских задач используем меньший пул
            engine_kwargs['pool_size'] = min(2, engine_kwargs['pool_size'])
        
        # Используем параметр connect_args для отличия админского пула
        connect_args = engine_kwargs.get('connect_args', {})
        connect_args['application_name'] = f"family_admin_{config.DB_USERNAME}"
        engine_kwargs['connect_args'] = connect_args
        
        logger.debug(f"Создание административного движка для пользователя {config.DB_USERNAME}")
    else:
        # Для обычных задач устанавливаем схему по умолчанию
        if hasattr(config, 'DB_SCHEMA') and config.DB_SCHEMA:
            # Добавляем имя схемы к опциям подключения
            connect_args = engine_kwargs.get('connect_args', {})
            connect_args['options'] = f"-c search_path={config.DB_SCHEMA}"
            engine_kwargs['connect_args'] = connect_args
            
            logger.debug(f"Установлена схема по умолчанию: {config.DB_SCHEMA}")
    
    engine = create_engine(
        connection_url,
        **engine_kwargs
    )
    
    return engine


def is_admin_engine(engine):
    """
    Проверяет, является ли движок административным (имеет права на создание таблиц).
    
    Args:
        engine: SQLAlchemy Engine для проверки
        
    Returns:
        bool: True, если движок имеет административные права
    """
    # Проверяем логин пользователя
    username = engine.url.username
    # family_admin или другие пользователи с именем, содержащим admin,
    # считаются административными
    return username == 'family_admin' or 'admin' in username.lower()


def ensure_schema_exists(engine, schema_name):
    """
    Проверяет существование схемы в базе данных. Не создает схему,
    только проверяет её наличие.
    
    Args:
        engine: SQLAlchemy Engine для подключения к БД
        schema_name (str): Имя схемы для проверки
        
    Returns:
        bool: True, если схема существует
    """
    try:
        inspector = inspect(engine)
        schemas = inspector.get_schema_names()
        return schema_name in schemas
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при проверке существования схемы {schema_name}: {e}")
        return False


def verify_table_access(engine, schema_name, table_name):
    """
    Проверяет доступ пользователя к таблице (права на чтение/запись).
    
    Args:
        engine: SQLAlchemy Engine для подключения к БД
        schema_name (str): Имя схемы
        table_name (str): Имя таблицы
        
    Returns:
        dict: Словарь с информацией о доступных правах (select, insert, update, delete)
    """
    try:
        with engine.connect() as conn:
            # Проверяем существование таблицы
            inspector = inspect(engine)
            if not table_name in inspector.get_table_names(schema=schema_name):
                return {
                    "exists": False, 
                    "select": False, 
                    "insert": False, 
                    "update": False, 
                    "delete": False
                }
            
            # Проверяем права на SELECT
            try:
                conn.execute(text(f"SELECT 1 FROM {schema_name}.{table_name} LIMIT 0"))
                select_access = True
            except SQLAlchemyError:
                select_access = False
            
            # Проверяем права на INSERT
            insert_access = False
            try:
                # Используем прямой запрос для проверки прав на INSERT
                result = conn.execute(text(f"""
                    SELECT has_table_privilege(
                        current_user, 
                        '{schema_name}.{table_name}', 
                        'INSERT'
                    )
                """)).scalar()
                insert_access = bool(result)
            except SQLAlchemyError:
                insert_access = False
            
            # Проверяем права на UPDATE
            update_access = False
            try:
                result = conn.execute(text(f"""
                    SELECT has_table_privilege(
                        current_user, 
                        '{schema_name}.{table_name}', 
                        'UPDATE'
                    )
                """)).scalar()
                update_access = bool(result)
            except SQLAlchemyError:
                update_access = False
            
            # Проверяем права на DELETE
            delete_access = False
            try:
                result = conn.execute(text(f"""
                    SELECT has_table_privilege(
                        current_user, 
                        '{schema_name}.{table_name}', 
                        'DELETE'
                    )
                """)).scalar()
                delete_access = bool(result)
            except SQLAlchemyError:
                delete_access = False
            
            # Возвращаем результат проверки прав
            return {
                "exists": True,
                "select": select_access,
                "insert": insert_access,
                "update": update_access,
                "delete": delete_access
            }
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при проверке прав доступа к таблице {schema_name}.{table_name}: {e}")
        return {
            "exists": False, 
            "select": False, 
            "insert": False, 
            "update": False, 
            "delete": False,
            "error": str(e)
        }


def verify_pgvector_support(engine):
    """
    Проверяет поддержку расширения pgvector в текущей базе данных.
    
    Args:
        engine: SQLAlchemy Engine для подключения к БД
        
    Returns:
        bool: True, если pgvector поддерживается
    """
    try:
        with engine.connect() as conn:
            # Проверяем наличие расширения vector
            result = conn.execute(text(
                "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
            )).scalar()
            
            return result > 0
    except SQLAlchemyError:
        return False


def grant_table_access(admin_engine, schema_name, table_name, user_name, 
                      grant_select=True, grant_insert=True, 
                      grant_update=True, grant_delete=True):
    """
    Предоставляет пользователю права доступа к таблице.
    Должен вызываться только с административным движком.
    
    Args:
        admin_engine: SQLAlchemy Engine с правами администратора
        schema_name (str): Имя схемы
        table_name (str): Имя таблицы
        user_name (str): Имя пользователя, которому предоставляются права
        grant_select (bool): Предоставить право на SELECT
        grant_insert (bool): Предоставить право на INSERT
        grant_update (bool): Предоставить право на UPDATE
        grant_delete (bool): Предоставить право на DELETE
        
    Returns:
        bool: True, если права успешно предоставлены
    """
    # Проверяем, что движок имеет права администратора
    if not is_admin_engine(admin_engine):
        logger.error("Попытка выдать права с неадминистративным движком")
        return False
    
    try:
        with admin_engine.connect() as conn:
            permissions = []
            if grant_select:
                permissions.append("SELECT")
            if grant_insert:
                permissions.append("INSERT")
            if grant_update:
                permissions.append("UPDATE")
            if grant_delete:
                permissions.append("DELETE")
                
            if not permissions:
                logger.warning("Не указаны права для предоставления")
                return False
                
            permissions_str = ", ".join(permissions)
            
            # Выдаем права на таблицу
            conn.execute(text(f"""
                GRANT {permissions_str} ON {schema_name}.{table_name} TO {user_name}
            """))
            conn.commit()
            
            logger.info(f"Права {permissions_str} на таблицу {schema_name}.{table_name} предоставлены пользователю {user_name}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при предоставлении прав доступа: {e}")
        return False