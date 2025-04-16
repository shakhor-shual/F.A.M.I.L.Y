"""
Базовые классы для моделей SQLAlchemy.

Этот модуль содержит базовый класс для моделей данных,
который может работать с любой указанной схемой в базе данных.
Включает интеграцию с менеджером схем для безопасного управления 
доступом к схемам и пользователями БД.
"""

import os
import logging
from sqlalchemy import MetaData, inspect, event, DDL
from sqlalchemy.orm import declarative_base
from typing import Optional, Tuple

from ..config import load_config, Config
from .schema_manager import get_schema_manager, SchemaManager

logger = logging.getLogger(__name__)


def create_base(schema_name: Optional[str] = None, 
               auto_create_schema: bool = True,
               use_admin: bool = False, 
               admin_credentials: Optional[Tuple[str, str]] = None,
               config: Optional[Config] = None):
    """
    Создает базовый класс для моделей SQLAlchemy с указанной схемой.
    
    Args:
        schema_name (str, optional): Имя схемы в базе данных. 
                                  Если не указано, берется из конфигурации.
        auto_create_schema (bool): Автоматически создавать схему при инициализации,
                                 если она не существует.
        use_admin (bool): Использовать учетную запись администратора для доступа к схеме.
        admin_credentials (Tuple[str, str]): Пара (admin_user, admin_password) для учетной 
                                          записи администратора. Необходима для создания схемы.
        config (Config, optional): Конфигурация подключения к БД.
        
    Returns:
        DeclarativeMeta: Базовый класс для моделей SQLAlchemy
    """
    # Загружаем конфигурацию, если не передана
    config = config or load_config()
    
    # Если схема не указана, берем из конфигурации
    if schema_name is None:
        schema_name = config.DB_SCHEMA
    
    # Получаем менеджер схем
    schema_manager = get_schema_manager(config)
    
    # Если переданы учетные данные, устанавливаем их в менеджере схем
    if admin_credentials:
        admin_user, admin_password = admin_credentials
        schema_manager.set_admin_credentials(admin_user, admin_password)
    
    # Если указано автоматическое создание схемы, проверяем её наличие
    # В тестовом окружении пропускаем создание схемы при загрузке модуля,
    # чтобы избежать ошибок при инициализации тестов
    is_test_environment = 'PYTEST_CURRENT_TEST' in os.environ
    
    if auto_create_schema and not is_test_environment and admin_credentials:
        try:
            # Создаем базу данных, если её нет
            schema_manager.create_database()
            
            # Создаем схему, если её нет
            if not schema_manager.schema_exists(schema_name):
                logger.info(f"Схема {schema_name} не существует. Создаем...")
                schema_manager.create_schema(schema_name, user_password="secure_password")
        except Exception as e:
            logger.warning(f"Не удалось создать схему {schema_name}: {e}")
    
    # Специальное соглашение для именования constraints
    naming_convention = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
    
    # Создаем метаданные с указанной схемой
    metadata = MetaData(schema=schema_name, naming_convention=naming_convention)
    DeclarativeBase = declarative_base(metadata=metadata)
    
    # Добавляем метод, который позволяет удобно получать название схемы
    @classmethod
    def get_schema_name(cls):
        """Возвращает имя схемы, используемой этим базовым классом."""
        return cls.metadata.schema
    
    # Добавляем метод, который возвращает имя пользователя для схемы
    @classmethod
    def get_schema_user(cls):
        """Возвращает имя пользователя для работы с этой схемой."""
        return f"{cls.get_schema_name()}_user"
    
    # Добавляем метод для создания движка специфичного для данной схемы
    @classmethod
    def create_engine(cls, use_admin=False, config=None, admin_credentials=None):
        """
        Создает SQLAlchemy движок для работы с этой схемой.
        
        Args:
            use_admin (bool): Использовать учетную запись администратора
            config (Config): Конфигурация базы данных
            admin_credentials (tuple): Пара (admin_user, admin_password)
        
        Returns:
            sqlalchemy.engine.Engine: Движок для работы с БД
        """
        config = config or load_config()
        schema_manager = get_schema_manager(config)
        
        # Если переданы учетные данные администратора, устанавливаем их
        if admin_credentials and use_admin:
            admin_user, admin_password = admin_credentials
            schema_manager.set_admin_credentials(admin_user, admin_password)
        
        return schema_manager.create_engine_for_schema(
            cls.get_schema_name(), 
            use_admin=use_admin
        )
    
    # Добавляем методы в класс
    DeclarativeBase.get_schema_name = get_schema_name
    DeclarativeBase.get_schema_user = get_schema_user
    DeclarativeBase.create_engine = create_engine
    
    if auto_create_schema:
        # Регистрируем событие для создания схемы при первом подключении
        @event.listens_for(metadata, 'before_create')
        def create_schema_if_not_exists(target, connection, **kw):
            schema = target.schema
            if schema:
                # Проверяем существование схемы
                inspector = inspect(connection)
                if not schema in inspector.get_schema_names():
                    logger.info(f"Создание схемы {schema} (она отсутствует в базе данных)")
                    connection.execute(DDL(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
                    logger.info(f"Схема {schema} успешно создана")
                else:
                    logger.debug(f"Схема {schema} уже существует")
    
    return DeclarativeBase


def initialize_base_with_schema(schema_name: Optional[str] = None, 
                             auto_create_schema: bool = True,
                             use_admin: bool = False,
                             admin_credentials: Optional[Tuple[str, str]] = None,
                             config: Optional[Config] = None):
    """
    Инициализирует и возвращает базовый класс с указанной схемой.
    
    Этот метод используется для удобного создания базовых классов
    с различными схемами в разных частях приложения.
    
    Args:
        schema_name (str, optional): Имя схемы. Если не указано, из конфигурации.
        auto_create_schema (bool): Создавать схему, если не существует
        use_admin (bool): Использовать учетную запись администратора
        admin_credentials (Tuple[str, str]): Пара (admin_user, admin_password)
        config (Config): Конфигурация базы данных
        
    Returns:
        DeclarativeMeta: Базовый класс для моделей SQLAlchemy с указанной схемой
    """
    config = config or load_config()
    
    # Если требуется автоматическое создание схемы и переданы учетные данные
    if auto_create_schema and admin_credentials:
        schema_manager = get_schema_manager(config)
        admin_user, admin_password = admin_credentials
        schema_manager.set_admin_credentials(admin_user, admin_password)
        
        # Создаем базу данных, если её нет
        schema_manager.create_database()
        
        if not schema_manager.schema_exists(schema_name):
            # Автоматически создаем схему
            schema_manager.create_schema(schema_name, user_password="secure_password")
    
    return create_base(
        schema_name=schema_name,
        auto_create_schema=auto_create_schema,
        use_admin=use_admin,
        admin_credentials=admin_credentials,
        config=config
    )


# Создание базового класса с настройками по умолчанию
Base = create_base()

# Публичное API модуля
__all__ = ['Base', 'create_base', 'initialize_base_with_schema']