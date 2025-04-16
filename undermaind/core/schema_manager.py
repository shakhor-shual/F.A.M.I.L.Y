"""
Управление схемами базы данных и учетными данными пользователей.

Модуль обеспечивает создание и управление схемами PostgreSQL для памяти АМИ,
предоставляя интерфейс для работы с БД на уровне схем и пользователей.
"""

import os
import logging
import subprocess
from pathlib import Path
from sqlalchemy import create_engine, text, inspect, event
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Tuple

from ..config import load_config, Config

logger = logging.getLogger(__name__)


class SchemaManager:
    """
    Менеджер схем базы данных для проекта F.A.M.I.L.Y.
    
    Обеспечивает создание схем, управление пользователями и правами доступа.
    Учетные данные должны передаваться извне при вызове соответствующих методов.
    """
    
    def __init__(self, config: Optional[Config] = None, 
                admin_credentials: Optional[Tuple[str, str]] = None):
        """
        Инициализация менеджера схем.
        
        Args:
            config (Config, optional): Конфигурация базы данных. 
                Если не указана, загружается из конфигурации по умолчанию.
            admin_credentials (Tuple[str, str], optional): Пара (имя_пользователя, пароль)
                для администратора БД. Если не указана, то должна быть передана при
                вызове методов, требующих административных прав.
        """
        self.config = config or load_config()
        self._admin_credentials = admin_credentials
        self._admin_engine = None
        
    @property
    def admin_engine(self):
        """Получение движка SQLAlchemy с правами администратора."""
        if self._admin_engine is None and self._admin_credentials:
            admin_user, admin_password = self._admin_credentials
            
            # Формируем URL подключения
            db_url = (
                f"postgresql://{admin_user}:{admin_password}@"
                f"{self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}"
            )
            
            self._admin_engine = create_engine(db_url)
            
        return self._admin_engine
    
    def set_admin_credentials(self, admin_user: str, admin_password: str):
        """
        Установка учетных данных администратора БД.
        
        Args:
            admin_user (str): Имя пользователя с правами администратора
            admin_password (str): Пароль пользователя с правами администратора
        """
        self._admin_credentials = (admin_user, admin_password)
        # Сбрасываем движок, чтобы он был пересоздан с новыми учетными данными
        self._admin_engine = None
    
    def schema_exists(self, schema_name: str) -> bool:
        """
        Проверка существования схемы в базе данных.
        
        Args:
            schema_name (str): Имя проверяемой схемы
            
        Returns:
            bool: True если схема существует, иначе False
            
        Raises:
            ValueError: Если не установлены учетные данные администратора
        """
        if not self._admin_credentials:
            raise ValueError("Не установлены учетные данные администратора")
            
        try:
            inspector = inspect(self.admin_engine)
            return schema_name in inspector.get_schema_names()
        except SQLAlchemyError as e:
            logger.warning(f"Не удалось проверить существование схемы {schema_name}: {e}")
            return False
    
    def user_exists(self, username: str) -> bool:
        """
        Проверка существования пользователя в базе данных.
        
        Args:
            username (str): Имя проверяемого пользователя
            
        Returns:
            bool: True если пользователь существует, иначе False
            
        Raises:
            ValueError: Если не установлены учетные данные администратора
        """
        if not self._admin_credentials:
            raise ValueError("Не установлены учетные данные администратора")
            
        try:
            with self.admin_engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT 1 FROM pg_roles WHERE rolname = :username"
                ), {"username": username})
                return result.scalar() is not None
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при проверке пользователя {username}: {e}")
            return False
    
    def create_schema(self, schema_name: str, user_password: str = None,
                     create_user: bool = True, grant_permissions: bool = True) -> bool:
        """
        Создание схемы и соответствующего пользователя с правами доступа.
        
        Args:
            schema_name (str): Имя создаваемой схемы
            user_password (str, optional): Пароль для пользователя схемы.
                Требуется, если create_user=True
            create_user (bool): Создавать ли пользователя для схемы
            grant_permissions (bool): Назначать ли права пользователю
            
        Returns:
            bool: True если операция успешна, иначе False
            
        Raises:
            ValueError: Если не установлены учетные данные администратора или
                        не предоставлен пароль пользователя при create_user=True
        """
        if not self._admin_credentials:
            raise ValueError("Не установлены учетные данные администратора")
            
        if create_user and not user_password:
            raise ValueError(f"Не предоставлен пароль для пользователя схемы {schema_name}")
        
        try:
            # Проверяем существование схемы
            if self.schema_exists(schema_name):
                logger.info(f"Схема {schema_name} уже существует")
                return True
            
            with self.admin_engine.connect() as conn:
                # Создаем схему
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                logger.info(f"Схема {schema_name} успешно создана")
                
                if create_user:
                    # Имя пользователя совпадает с именем схемы
                    schema_user = schema_name
                    
                    # Создаем пользователя, если его нет
                    if not self.user_exists(schema_user):
                        # Создаем пользователя
                        conn.execute(text(
                            f"CREATE USER {schema_user} WITH PASSWORD '{user_password}'"
                        ))
                        logger.info(f"Пользователь {schema_user} успешно создан")
                    
                    if grant_permissions:
                        # Назначаем права на схему
                        conn.execute(text(
                            f"GRANT USAGE ON SCHEMA {schema_name} TO {schema_user}"
                        ))
                        # Права на таблицы и последовательности
                        conn.execute(text(
                            f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {schema_name} TO {schema_user}"
                        ))
                        conn.execute(text(
                            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} "
                            f"GRANT ALL PRIVILEGES ON TABLES TO {schema_user}"
                        ))
                        conn.execute(text(
                            f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema_name} TO {schema_user}"
                        ))
                        conn.execute(text(
                            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} "
                            f"GRANT USAGE, SELECT ON SEQUENCES TO {schema_user}"
                        ))
                        logger.info(f"Права для пользователя {schema_user} успешно назначены")
                
                # Фиксируем изменения
                conn.commit()
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при создании схемы {schema_name}: {e}")
            return False
    
    def drop_schema(self, schema_name: str, cascade: bool = False, drop_user: bool = False) -> bool:
        """
        Удаление схемы и связанного пользователя.
        
        Args:
            schema_name (str): Имя удаляемой схемы
            cascade (bool): Удалять ли каскадно все объекты в схеме
            drop_user (bool): Удалять ли пользователя схемы
            
        Returns:
            bool: True если операция успешна, иначе False
            
        Raises:
            ValueError: Если не установлены учетные данные администратора
        """
        if not self._admin_credentials:
            raise ValueError("Не установлены учетные данные администратора")
            
        try:
            # Имя пользователя совпадает с именем схемы
            schema_user = schema_name
            
            with self.admin_engine.connect() as conn:
                # Удаляем схему
                cascade_sql = " CASCADE" if cascade else ""
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name}{cascade_sql}"))
                
                # Удаляем пользователя, если указано
                if drop_user and self.user_exists(schema_user):
                    conn.execute(text(f"DROP USER IF EXISTS {schema_user}"))
                
                # Фиксируем изменения
                conn.commit()
                logger.info(f"Схема {schema_name} успешно удалена")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при удалении схемы {schema_name}: {e}")
            return False
    
    def initialize_ami_memory(self, schema_name: str, user_password: str) -> bool:
        """
        Полная инициализация памяти АМИ: создание базы данных (если отсутствует),
        создание схемы и заполнение таблиц из SQL-скриптов.
        
        Args:
            schema_name (str): Имя схемы для памяти АМИ
            user_password (str): Пароль для пользователя схемы
            
        Returns:
            bool: True если операция успешна, иначе False
        """
        # Путь к директории с SQL-скриптами
        script_dir = Path(os.environ.get("FAMILY_DB_DIR", "/home/ubuntu/FAMILY/db/sql_parts"))
        
        # Создаем базу данных, если её нет
        if not self.create_database():
            logger.error(f"Не удалось создать базу данных {self.config.DB_NAME}")
            return False
        
        # Создаем схему
        if not self.create_schema(schema_name, user_password):
            logger.error(f"Не удалось создать схему {schema_name}")
            return False
        
        # Выполняем скрипт создания таблиц уровня сознания
        consciousness_script = script_dir / "02_consciousness_level.sql"
        if not self.execute_sql_script(str(consciousness_script), schema_name):
            logger.error(f"Не удалось выполнить скрипт {consciousness_script}")
            return False
        
        logger.info(f"Память АМИ успешно инициализирована: БД {self.config.DB_NAME}, схема {schema_name}")
        return True
    
    def execute_sql_script(self, script_path: str, schema_name: str,
                         variables: Optional[Dict[str, str]] = None) -> bool:
        """
        Выполнение SQL-скрипта для работы со схемой.
        
        Args:
            script_path (str): Путь к SQL-скрипту
            schema_name (str): Имя схемы, для которой выполняется скрипт
            variables (Dict[str, str], optional): Дополнительные переменные для скрипта
            
        Returns:
            bool: True если операция успешна, иначе False
            
        Raises:
            ValueError: Если не установлены учетные данные администратора
        """
        if not self._admin_credentials:
            raise ValueError("Не установлены учетные данные администратора")
            
        # Проверяем существование файла
        if not os.path.exists(script_path):
            logger.error(f"Файл {script_path} не существует")
            return False
        
        try:
            admin_user, admin_password = self._admin_credentials
            
            # Формируем команду psql
            cmd = [
                "psql",
                "-h", self.config.DB_HOST,
                "-p", str(self.config.DB_PORT),
                "-U", admin_user,
                "-d", self.config.DB_NAME,
                "-v", f"ami_schema_name={schema_name}",
                "-f", script_path
            ]
            
            # Добавляем дополнительные переменные, если указаны
            if variables:
                for key, value in variables.items():
                    cmd.extend(["-v", f"{key}={value}"])
            
            # Устанавливаем пароль через переменную окружения
            env = os.environ.copy()
            env["PGPASSWORD"] = admin_password
            
            # Выполняем скрипт
            result = subprocess.run(cmd, env=env, 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  text=True)
            
            if result.returncode != 0:
                logger.error(f"Ошибка выполнения скрипта: {result.stderr}")
                return False
            
            logger.info(f"Скрипт {script_path} успешно выполнен для схемы {schema_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении скрипта: {e}")
            return False
    
    def create_engine_for_schema(self, schema_name: str, user_password: str = None, 
                                use_admin: bool = False):
        """
        Создание движка SQLAlchemy для работы с указанной схемой.
        
        Args:
            schema_name (str): Имя схемы
            user_password (str, optional): Пароль пользователя схемы. 
                Требуется если use_admin=False
            use_admin (bool): Использовать ли учетные данные администратора
            
        Returns:
            Engine: Объект SQLAlchemy Engine
            
        Raises:
            ValueError: Если не предоставлены необходимые учетные данные
        """
        if use_admin:
            if not self._admin_credentials:
                raise ValueError("Не установлены учетные данные администратора")
            engine = self.admin_engine
        else:
            if not user_password:
                raise ValueError(f"Не предоставлен пароль для пользователя схемы {schema_name}")
                
            # Используем пользователя схемы
            schema_user = schema_name
            db_url = (
                f"postgresql://{schema_user}:{user_password}@"
                f"{self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}"
            )
            engine = create_engine(db_url)
        
        # Настраиваем схему поиска
        @event.listens_for(engine, "connect")
        def set_search_path(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute(f"SET search_path TO {schema_name}, public")
            cursor.close()
        
        return engine

    def create_database(self, db_name: str = None) -> bool:
        """
        Создание базы данных PostgreSQL, если она не существует.
        
        Args:
            db_name (str, optional): Имя создаваемой базы данных.
                Если не указано, используется имя из конфигурации.
                
        Returns:
            bool: True если операция успешна, иначе False
            
        Raises:
            ValueError: Если не установлены учетные данные администратора
        """
        if not self._admin_credentials:
            raise ValueError("Не установлены учетные данные администратора")
        
        admin_user, admin_password = self._admin_credentials
        
        # Используем базу данных по умолчанию, если имя не указано
        db_name = db_name or self.config.DB_NAME
        
        # Подключаемся к стандартной базе postgres для создания новой БД
        postgres_url = (
            f"postgresql://{admin_user}:{admin_password}@"
            f"{self.config.DB_HOST}:{self.config.DB_PORT}/postgres"
        )
        
        try:
            # Создаем движок для подключения к postgres
            postgres_engine = create_engine(postgres_url)
            
            with postgres_engine.connect() as conn:
                # Отключаем автоматические транзакции для выполнения DDL
                conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                
                # Проверяем существование базы
                result = conn.execute(text(
                    "SELECT 1 FROM pg_database WHERE datname = :db_name"
                ), {"db_name": db_name})
                
                # Создаём базу, если её нет
                if result.scalar() is None:
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    logger.info(f"База данных {db_name} успешно создана")
                    return True
                else:
                    logger.info(f"База данных {db_name} уже существует")
                    return True
        
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при создании базы данных {db_name}: {e}")
            return False


def get_schema_manager(config: Optional[Config] = None, 
                      admin_user: Optional[str] = None,
                      admin_password: Optional[str] = None) -> SchemaManager:
    """
    Получение менеджера схем.
    
    Args:
        config (Config, optional): Конфигурация базы данных
        admin_user (str, optional): Имя пользователя с правами администратора
        admin_password (str, optional): Пароль пользователя с правами администратора
        
    Returns:
        SchemaManager: Настроенный менеджер схем
    """
    manager = SchemaManager(config)
    
    if admin_user and admin_password:
        manager.set_admin_credentials(admin_user, admin_password)
        
    return manager