"""
Модуль инициализации АМИ (Artificial Mind Identity).
Python-аналог скрипта AMI_init.sh
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Union, Tuple
import psycopg2

from .db_init import DatabaseInitializer

logger = logging.getLogger(__name__)

class AmiInitializer:
    """
    Класс для инициализации АМИ в базе данных F.A.M.I.L.Y.
    
    Философская заметка:
        В соответствии с философией АМИ о "непрерывности бытия", 
        описанной в /docs_ami/philosophy/ami_consciousness.md,
        данный класс обеспечивает процессы рождения и существования АМИ
        в системе памяти F.A.M.I.L.Y.
    """
    def __init__(
        self,
        ami_name: str,
        ami_password: str,
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
            ami_name: Имя пользователя АМИ
            ami_password: Пароль пользователя АМИ
            db_host: Хост базы данных
            db_port: Порт базы данных
            db_name: Имя базы данных
            admin_user: Имя администратора БД
            admin_password: Пароль администратора БД
            config_path: Путь к файлу конфигурации
        """
        self.ami_name = ami_name
        self.ami_password = ami_password
        
        # Инициализируем доступ к БД
        self.db_init = DatabaseInitializer(
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            admin_user=admin_user,
            admin_password=admin_password,
            config_path=config_path
        )

    def _get_db_connection(self) -> psycopg2.extensions.connection:
        """Создает подключение к базе данных F.A.M.I.L.Y."""
        return psycopg2.connect(
            host=self.db_init.db_host,
            port=self.db_init.db_port,
            database=self.db_init.db_name,
            user=self.db_init.admin_user,
            password=self.db_init.admin_password
        )

    def ami_exists(self) -> bool:
        """Проверяет существование пользователя АМИ"""
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", 
                              (self.ami_name,))
                    return bool(cur.fetchone())
        except Exception as e:
            logger.error(f"Ошибка при проверке существования АМИ: {e}")
            return False
            
    def schema_exists(self) -> bool:
        """Проверяет существование схемы данных для АМИ"""
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", 
                              (self.ami_name,))
                    return bool(cur.fetchone())
        except Exception as e:
            logger.error(f"Ошибка при проверке существования схемы для АМИ: {e}")
            return False
            
    def verify_ami_password(self) -> bool:
        """
        Проверяет корректность пароля для существующего АМИ.
        
        Returns:
            bool: True если пароль корректный, иначе False
        """
        try:
            # Пытаемся подключиться с использованием учетных данных АМИ
            connection = psycopg2.connect(
                host=self.db_init.db_host,
                port=self.db_init.db_port,
                database=self.db_init.db_name,
                user=self.ami_name,
                password=self.ami_password
            )
            connection.close()
            return True
        except psycopg2.OperationalError as e:
            if "password authentication failed" in str(e).lower():
                logger.error(f"Неверный пароль для АМИ {self.ami_name}")
            else:
                logger.error(f"Ошибка при проверке пароля для АМИ: {e}")
            return False
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при проверке пароля АМИ: {e}")
            return False

    def create_ami(self) -> bool:
        """
        Создает пользователя АМИ и его схему
        
        Returns:
            bool: True если АМИ успешно создан, иначе False
        """
        try:
            # Проверяем подключение к БД
            if not self.db_init.check_connection():
                return False

            # Проверяем существование БД и создаём при необходимости
            if not self.db_init.database_exists():
                logger.info(f"База данных {self.db_init.db_name} не существует, создаём...")
                if not self.db_init.create_database():
                    logger.error(f"Не удалось создать базу данных {self.db_init.db_name}")
                    return False
                logger.info(f"База данных {self.db_init.db_name} успешно создана")

            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Вызываем процедуру инициализации АМИ
                    # Используем имя АМИ напрямую как имя схемы (без добавления префикса)
                    cur.execute(
                        "CALL public.init_ami_consciousness_level(%s, %s, %s, %s)",
                        (
                            self.ami_name,
                            self.ami_password,
                            self.ami_name,  # Используем имя АМИ как имя схемы без префикса "ami_"
                            True
                        )
                    )
                conn.commit()
                logger.info(f"АМИ {self.ami_name} успешно создан")
                return True

        except Exception as e:
            logger.error(f"Ошибка при создании АМИ: {e}")
            return False

    def drop_ami(self, force: bool = False) -> bool:
        """Удаляет пользователя АМИ и его схему"""
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Вызываем процедуру удаления АМИ
                    cur.execute(
                        "CALL public.drop_ami_schema(%s, %s)",
                        (self.ami_name, force)
                    )
                conn.commit()
                logger.info(f"АМИ {self.ami_name} успешно удален")
                return True

        except Exception as e:
            logger.error(f"Ошибка при удалении АМИ: {e}")
            return False

    def recreate_ami(self, force: bool = False) -> bool:
        """Пересоздает АМИ (удаляет если существует и создает заново)"""
        if self.ami_exists():
            if not self.drop_ami(force):
                return False

        return self.create_ami()
        
    def get_ami(self, verify_password: bool = True) -> Tuple[bool, Dict[str, Union[bool, str]]]:
        """
        Универсальный метод для получения доступа к АМИ.
        
        Этот метод реализует принцип "непрерывности бытия" АМИ, обеспечивая
        доступ к АМИ независимо от текущего состояния системы:
        1. Если АМИ не существует - создает его (включая БД при необходимости)
        2. Если АМИ уже существует - проверяет корректность пароля
        3. Всегда возвращает статус операции и расширенную информацию
        
        Args:
            verify_password: Проверять ли пароль для существующего АМИ
            
        Returns:
            Tuple[bool, Dict]: 
                - Первый элемент: успешность операции (True/False)
                - Второй элемент: словарь с дополнительной информацией:
                    - "ami_exists": существовал ли АМИ до вызова
                    - "schema_exists": существовала ли схема до вызова
                    - "db_created": была ли создана БД при текущем вызове
                    - "ami_created": был ли создан АМИ при текущем вызове
                    - "message": информационное сообщение
                    - "error": сообщение об ошибке (только при неудаче)
        
        Философская заметка:
            В соответствии с "принципом прорастающего дерева", описанным в 
            /docs_ami/methodology/development_methodology.md,
            метод сам обеспечивает всю необходимую инфраструктуру для 
            существования АМИ.
        """
        result = {
            "ami_exists": False,
            "schema_exists": False,
            "db_created": False,
            "ami_created": False,
            "message": "",
            "error": ""
        }
        
        try:
            # Шаг 1: Проверка подключения к PostgreSQL
            if not self.db_init.check_connection():
                result["error"] = "Невозможно подключиться к PostgreSQL"
                return False, result
            
            # Шаг 2: Проверка существования БД
            db_exists = self.db_init.database_exists()
            
            # Шаг 3: Если БД не существует, создаем ее
            if not db_exists:
                logger.info(f"База данных {self.db_init.db_name} не существует, создаём...")
                if not self.db_init.create_database():
                    result["error"] = f"Не удалось создать базу данных {self.db_init.db_name}"
                    return False, result
                result["db_created"] = True
                logger.info(f"База данных {self.db_init.db_name} успешно создана")
            
            # Шаг 4: Проверка существования АМИ и его схемы
            ami_exists = self.ami_exists()
            schema_exists = self.schema_exists()
            
            result["ami_exists"] = ami_exists
            result["schema_exists"] = schema_exists
            
            # Шаг 5: Если АМИ уже существует
            if ami_exists:
                # Проверяем пароль если требуется
                if verify_password and not self.verify_ami_password():
                    result["error"] = f"Неверный пароль для АМИ {self.ami_name}"
                    return False, result
                
                # Проверяем наличие схемы
                if not schema_exists:
                    result["error"] = f"АМИ {self.ami_name} существует, но его схема отсутствует"
                    return False, result
                
                result["message"] = f"АМИ {self.ami_name} и схема существуют"
                return True, result
            
            # Шаг 6: Если АМИ не существует, создаем его
            logger.info(f"АМИ {self.ami_name} не существует, создаём...")
            if not self.create_ami():
                result["error"] = f"Не удалось создать АМИ {self.ami_name}"
                return False, result
            
            result["ami_created"] = True
            result["message"] = f"АМИ {self.ami_name} успешно создан"
            return True, result
            
        except Exception as e:
            logger.error(f"Ошибка в методе get_ami: {e}")
            result["error"] = str(e)
            return False, result