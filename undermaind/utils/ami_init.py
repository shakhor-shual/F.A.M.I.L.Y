"""
Модуль инициализации АМИ (Artificial Mind Identity).
Python-аналог скрипта AMI_init.sh
"""

import os
import logging
from pathlib import Path
from typing import Optional
import psycopg2

from .db_init import DatabaseInitializer

logger = logging.getLogger(__name__)

class AmiInitializer:
    """
    Класс для инициализации АМИ в базе данных F.A.M.I.L.Y.
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

    def create_ami(self) -> bool:
        """Создает пользователя АМИ и его схему"""
        try:
            # Проверяем подключение к БД
            if not self.db_init.check_connection():
                return False

            # Проверяем существование БД
            if not self.db_init.database_exists():
                logger.error(f"База данных {self.db_init.db_name} не существует")
                return False

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