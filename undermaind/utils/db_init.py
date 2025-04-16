"""
Модуль инициализации базы данных F.A.M.I.L.Y.
Python-аналог скрипта FAMILY_DB_init.sh
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """
    Класс для инициализации базы данных F.A.M.I.L.Y.
    """
    def __init__(
        self,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_name: str = "family_db",
        admin_user: str = "family_admin",
        admin_password: str = None,
        config_path: Optional[str] = None
    ):
        """
        Инициализация объекта.
        
        Args:
            db_host: Хост базы данных
            db_port: Порт базы данных
            db_name: Имя базы данных
            admin_user: Имя администратора
            admin_password: Пароль администратора
            config_path: Путь к файлу конфигурации
        """
        # Загрузка конфигурации если указан путь
        if config_path:
            self._load_config(config_path)
        else:
            self.db_host = db_host
            self.db_port = db_port
            self.db_name = db_name
            self.admin_user = admin_user
            self.admin_password = admin_password

        # Путь к SQL скриптам
        self.sql_scripts_dir = Path(os.getenv('FAMILY_SQL_DIR', 
            Path(__file__).parent.parent.parent / 'db' / 'sql_postgresql'))

    def _load_config(self, config_path: str) -> None:
        """Загрузка параметров из конфигурационного файла"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Конфигурационный файл не найден: {config_path}")
            
        config = {}
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"')
        
        self.db_host = config.get('FAMILY_DB_HOST', 'localhost')
        self.db_port = int(config.get('FAMILY_DB_PORT', '5432'))
        self.db_name = config.get('FAMILY_DB_NAME', 'family_db')
        self.admin_user = config.get('FAMILY_ADMIN_USER', 'family_admin')
        # Поддержка как старого, так и нового формата имен переменных для пароля
        self.admin_password = config.get('FAMILY_ADMIN_PASSWORD', config.get('FAMILY_ADMIN_PASS'))

    def _get_postgres_connection(self) -> psycopg2.extensions.connection:
        """Создает подключение к системной БД postgres"""
        return psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database="postgres",
            user=self.admin_user,
            password=self.admin_password
        )

    def _get_database_connection(self) -> psycopg2.extensions.connection:
        """Создает подключение к базе данных F.A.M.I.L.Y."""
        return psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.admin_user,
            password=self.admin_password
        )

    def check_connection(self) -> bool:
        """Проверяет возможность подключения к БД"""
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            return False

    def database_exists(self) -> bool:
        """Проверяет существование базы данных"""
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", 
                              (self.db_name,))
                    return bool(cur.fetchone())
        except Exception as e:
            logger.error(f"Ошибка при проверке существования БД: {e}")
            return False

    def create_admin_user(self) -> bool:
        """Создает пользователя-администратора если он не существует"""
        try:
            with self._get_postgres_connection() as conn:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                with conn.cursor() as cur:
                    # Проверяем существование пользователя
                    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", 
                              (self.admin_user,))
                    if not cur.fetchone():
                        # Создаем пользователя
                        cur.execute(
                            "CREATE USER %s WITH PASSWORD %s SUPERUSER CREATEDB CREATEROLE INHERIT LOGIN",
                            (psycopg2.extensions.AsIs(self.admin_user), self.admin_password)
                        )
                        logger.info(f"Пользователь {self.admin_user} успешно создан")
                    return True
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {e}")
            return False

    def create_database(self) -> bool:
        """Создает базу данных если она не существует"""
        try:
            if not self.database_exists():
                # Создаем подключение к системной БД postgres
                conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    database="postgres",
                    user=self.admin_user,
                    password=self.admin_password
                )
                
                # Отключаем автоматические транзакции
                conn.autocommit = True
                
                cur = conn.cursor()
                try:
                    cur.execute(f'CREATE DATABASE {self.db_name} OWNER {self.admin_user}')
                    logger.info(f"База данных {self.db_name} успешно создана")
                    return True
                    
                finally:
                    cur.close()
                    conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при создании базы данных: {e}")
            return False

    def drop_database(self, force: bool = False) -> bool:
        """
        Удаляет базу данных.
        
        Args:
            force: Принудительно отключить все активные подключения
            
        Returns:
            bool: True если операция успешна, иначе False
        """
        try:
            if self.database_exists():
                # Создаем подключение к системной БД postgres
                conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    database="postgres",
                    user=self.admin_user,
                    password=self.admin_password
                )
                
                # Отключаем автоматические транзакции
                conn.autocommit = True
                
                cur = conn.cursor()
                try:
                    if force:
                        # Отключаем активные подключения
                        cur.execute(
                            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                            f"WHERE datname = '{self.db_name}' AND pid <> pg_backend_pid()"
                        )
                    # Удаляем БД
                    cur.execute(f'DROP DATABASE {self.db_name}')
                    logger.info(f"База данных {self.db_name} успешно удалена")
                    return True
                    
                finally:
                    cur.close()
                    conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при удалении базы данных: {e}")
            return False

    def apply_sql_scripts(self, level_name: str) -> bool:
        """
        Применяет SQL скрипты для указанного уровня
        
        Args:
            level_name: Имя уровня (например, 'consciousness_level')
        """
        level_dir = self.sql_scripts_dir / level_name
        config_file = level_dir / 'init.conf'
        
        if not config_file.exists():
            logger.error(f"Файл конфигурации уровня не найден: {config_file}")
            return False
            
        try:
            with self._get_database_connection() as conn:
                with conn.cursor() as cur:
                    # Читаем список скриптов из конфигурации
                    with open(config_file) as f:
                        scripts = [line.strip() for line in f 
                                 if line.strip() and not line.startswith('#')]
                    
                    # Выполняем каждый скрипт
                    for script_name in scripts:
                        script_path = level_dir / script_name
                        if not script_path.exists():
                            logger.error(f"Скрипт не найден: {script_path}")
                            return False
                            
                        logger.info(f"Выполняем скрипт: {script_name}")
                        with open(script_path) as f:
                            # Читаем скрипт построчно и отфильтровываем команды psql
                            filtered_lines = []
                            for line in f:
                                # Пропускаем метакоманды psql (начинаются с \)
                                if line.strip().startswith('\\'):
                                    continue
                                filtered_lines.append(line)
                            
                            # Собираем отфильтрованный скрипт
                            script_content = ''.join(filtered_lines)
                            
                            if not script_content.strip():
                                logger.warning(f"Скрипт {script_name} пуст после фильтрации")
                                continue
                            
                            try:
                                # Выполняем скрипт как единый блок
                                cur.execute(script_content)
                                conn.commit()
                            except Exception as e:
                                conn.rollback()
                                logger.error(f"Ошибка при выполнении скрипта {script_name}: {e}")
                                return False
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Ошибка при выполнении SQL скриптов: {e}")
            return False

    def filter_procedure_scripts(self, scripts_list: List[str], level_dir: Path) -> List[str]:
        """
        Фильтрует список SQL-файлов, оставляя только те, которые содержат хранимые процедуры.
        
        Args:
            scripts_list: Список имен SQL-файлов для фильтрации
            level_dir: Путь к директории уровня, содержащей SQL-файлы
            
        Returns:
            List[str]: Отфильтрованный список имен файлов, содержащих CREATE OR REPLACE PROCEDURE/FUNCTION
        """
        procedure_scripts = []
        
        for script_name in scripts_list:
            script_path = level_dir / script_name
            if not script_path.exists():
                continue
                
            # Проверяем, содержит ли файл определения процедур или функций
            with open(script_path) as f:
                content = f.read().lower()
                if ("create or replace procedure" in content or 
                    "create or replace function" in content):
                    procedure_scripts.append(script_name)
        
        return procedure_scripts

    def initialize_database(self, recreate: bool = False, refresh_procedures: bool = True) -> bool:
        """
        Полная инициализация базы данных F.A.M.I.L.Y.
        
        Args:
            recreate: Пересоздать БД если существует
            refresh_procedures: Обновить хранимые процедуры даже если БД уже существует
        """
        try:
            # Проверяем подключение
            if not self.check_connection():
                return False
                
            # Создаем пользователя
            if not self.create_admin_user():
                return False
                
            # Удаляем БД если нужно
            if recreate and not self.drop_database(force=True):
                return False
                
            # Проверяем существование БД и создаем при необходимости
            db_existed = self.database_exists()
            if not db_existed and not self.create_database():
                return False
                
            # Получаем корневой конфиг для определения порядка уровней
            root_config = self.sql_scripts_dir / 'init.conf'
            if not root_config.exists():
                logger.error(f"Корневой конфиг не найден: {root_config}")
                return False
                
            # Читаем список уровней
            with open(root_config) as f:
                levels = [line.strip() for line in f 
                         if line.strip() and not line.startswith('#')]
            
            # Если база данных существовала и нужно только обновить процедуры
            if db_existed and not recreate and refresh_procedures:
                logger.info("База данных уже существует. Обновляем только хранимые процедуры.")
                if not self.refresh_stored_procedures():
                    return False
            # Иначе применяем все скрипты для каждого уровня
            else:
                for level in levels:
                    if not self.apply_sql_scripts(level):
                        return False
                    
            logger.info("Инициализация базы данных F.A.M.I.L.Y. успешно завершена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            return False

    def refresh_stored_procedures(self) -> bool:
        """
        Обновляет только хранимые процедуры в базе данных без затрагивания таблиц и других объектов.
        Соответствует поведению shell-скрипта при запуске без параметров recreate.
        
        Returns:
            bool: True если операция успешна, иначе False
        """
        try:
            # Проверяем существование БД
            if not self.database_exists():
                logger.error(f"База данных {self.db_name} не существует. Обновление процедур невозможно.")
                return False
                
            # Читаем корневой конфиг для определения порядка уровней
            root_config = self.sql_scripts_dir / 'init.conf'
            if not root_config.exists():
                logger.error(f"Корневой конфиг не найден: {root_config}")
                return False
                
            # Читаем список уровней
            with open(root_config) as f:
                levels = [line.strip() for line in f 
                         if line.strip() and not line.startswith('#')]
            
            logger.info("Запуск обновления хранимых процедур в БД F.A.M.I.L.Y...")
            
            # Для каждого уровня обновляем только процедуры и функции
            for level_name in levels:
                level_dir = self.sql_scripts_dir / level_name
                config_file = level_dir / 'init.conf'
                
                if not config_file.exists():
                    logger.warning(f"Файл конфигурации уровня не найден: {config_file}")
                    continue
                    
                # Читаем список всех скриптов из конфигурации уровня
                with open(config_file) as f:
                    all_scripts = [line.strip() for line in f 
                                 if line.strip() and not line.startswith('#')]
                
                # Фильтруем только скрипты с хранимыми процедурами
                procedure_scripts = self.filter_procedure_scripts(all_scripts, level_dir)
                
                if not procedure_scripts:
                    logger.info(f"В уровне {level_name} не найдено скриптов с хранимыми процедурами")
                    continue
                
                logger.info(f"Обновление {len(procedure_scripts)} хранимых процедур в уровне {level_name}")
                
                # Применяем только скрипты с процедурами
                with self._get_database_connection() as conn:
                    with conn.cursor() as cur:
                        for script_name in procedure_scripts:
                            script_path = level_dir / script_name
                            
                            logger.info(f"Обновление хранимой процедуры из скрипта: {script_name}")
                            with open(script_path) as f:
                                # Читаем скрипт построчно и отфильтровываем команды psql
                                filtered_lines = []
                                for line in f:
                                    # Пропускаем метакоманды psql (начинаются с \)
                                    if line.strip().startswith('\\'):
                                        continue
                                    filtered_lines.append(line)
                                
                                # Собираем отфильтрованный скрипт
                                script_content = ''.join(filtered_lines)
                                
                                if not script_content.strip():
                                    logger.warning(f"Скрипт {script_name} пуст после фильтрации")
                                    continue
                                
                                try:
                                    # Выполняем скрипт как единый блок
                                    cur.execute(script_content)
                                    conn.commit()
                                    logger.info(f"Хранимая процедура из скрипта {script_name} успешно обновлена")
                                except Exception as e:
                                    conn.rollback()
                                    logger.error(f"Ошибка при обновлении хранимой процедуры из скрипта {script_name}: {e}")
                                    return False
            
            logger.info("Обновление хранимых процедур в БД F.A.M.I.L.Y. успешно завершено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении хранимых процедур: {e}")
            return False