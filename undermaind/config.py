"""
Конфигурация для пакета UnderMaind.

Этот модуль обеспечивает загрузку и хранение параметров конфигурации
для подключения к базе данных и других настроек.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """
    Класс для хранения конфигурационных параметров.

    Атрибуты:
        DB_USERNAME (str): Имя пользователя базы данных
        DB_PASSWORD (str): Пароль для подключения к базе данных
        DB_HOST (str): Хост базы данных
        DB_PORT (int): Порт базы данных
        DB_NAME (str): Имя базы данных
        DB_SCHEMA (str): Схема базы данных для хранения памяти АМИ
        DB_ADMIN_USER (str): Имя пользователя с правами администратора БД
        DB_ADMIN_PASSWORD (str): Пароль пользователя-администратора
        DB_POOL_SIZE (int): Размер пула соединений
        DB_POOL_RECYCLE (int): Время (в секундах) для переиспользования соединений в пуле
        DB_ECHO_SQL (bool): Флаг вывода SQL-запросов в лог
        EMBEDDING_MODEL (str): Идентификатор модели для создания векторов
    """
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_SCHEMA: str
    DB_ADMIN_USER: Optional[str] = None
    DB_ADMIN_PASSWORD: Optional[str] = None
    DB_POOL_SIZE: int = 5
    DB_POOL_RECYCLE: int = 3600  # 1 час по умолчанию
    DB_ECHO_SQL: bool = False
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"


def load_config(config_file: Optional[str] = None, env_prefix: str = "UNDERMAIND_") -> Config:
    """
    Загружает конфигурацию из файла и/или переменных окружения.

    Args:
        config_file: Путь к файлу конфигурации (опционально)
        env_prefix: Префикс для переменных окружения (по умолчанию "UNDERMAIND_")

    Returns:
        Config: Объект конфигурации
    """
    # Значения по умолчанию
    config_values = {
        "DB_USERNAME": "postgres",
        "DB_PASSWORD": "",
        "DB_HOST": "localhost",
        "DB_PORT": 5432,
        "DB_NAME": "family_memory_db",
        "DB_SCHEMA": "memory",  # Обновлено: используем имя схемы без префикса ami_
        "DB_ADMIN_USER": os.environ.get("DB_ADMIN_USER", "postgres"),
        "DB_ADMIN_PASSWORD": os.environ.get("DB_ADMIN_PASSWORD", ""),
        "DB_POOL_SIZE": 5,
        "DB_POOL_RECYCLE": 3600,  # 1 час по умолчанию
        "DB_ECHO_SQL": False,
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    }

    # Загрузка из файла, если указан
    if config_file and os.path.exists(config_file):
        with open(config_file, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    if key in config_values:
                        # Преобразование типов
                        if key == "DB_PORT" or key == "DB_POOL_SIZE" or key == "DB_POOL_RECYCLE":
                            config_values[key] = int(value)
                        elif key == "DB_ECHO_SQL":
                            config_values[key] = value.lower() in ("true", "yes", "1")
                        else:
                            config_values[key] = value

    # Переопределение значениями из переменных окружения
    for key in config_values.keys():
        env_var = f"{env_prefix}{key}"
        if env_var in os.environ:
            value = os.environ[env_var]
            if key == "DB_PORT" or key == "DB_POOL_SIZE" or key == "DB_POOL_RECYCLE":
                config_values[key] = int(value)
            elif key == "DB_ECHO_SQL":
                config_values[key] = value.lower() in ("true", "yes", "1")
            else:
                config_values[key] = value

    # Создание объекта конфигурации
    return Config(**config_values)


# Сохраняем глобальный объект конфигурации для кеширования
_global_config = None

def get_config(config_file: Optional[str] = None, env_prefix: str = "UNDERMAIND_", reload: bool = False) -> Config:
    """
    Получает конфигурацию, используя кешированный объект или загружая конфигурацию заново.
    
    Args:
        config_file: Путь к файлу конфигурации (опционально)
        env_prefix: Префикс для переменных окружения (по умолчанию "UNDERMAIND_")
        reload: Если True, принудительно перезагружает конфигурацию

    Returns:
        Config: Объект конфигурации
    """
    global _global_config
    
    # Определяем путь к корню проекта
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Определяем пути к конфигурациям в корне проекта
    main_config_path = os.path.join(project_root, "family_config.env")
    test_config_path = os.path.join(project_root, "family_config_test.env")
    
    # Проверяем, в каком режиме работаем (тестирование или обычный режим)
    is_test_environment = os.environ.get("FAMILY_TEST_MODE", "false").lower() in ("true", "yes", "1")
    
    # Если принудительно перезагружаем или кэш пуст
    if reload or _global_config is None:
        # Определяем, какой файл конфигурации использовать
        active_config_path = test_config_path if is_test_environment else main_config_path
        
        # Если предоставлен пользовательский путь к конфигурации, используем его
        if config_file:
            active_config_path = config_file
        
        # Проверяем существование файла конфигурации
        if os.path.exists(active_config_path):
            # Загружаем переменные окружения из файла
            import dotenv
            dotenv.load_dotenv(active_config_path)
            
            # Создаем конфигурацию на основе загруженных параметров
            _global_config = Config(
                DB_USERNAME=os.environ.get("FAMILY_AMI_USER", "postgres"),
                DB_PASSWORD=os.environ.get("FAMILY_AMI_PASSWORD", ""),
                DB_HOST=os.environ.get("FAMILY_DB_HOST", "localhost"),
                DB_PORT=int(os.environ.get("FAMILY_DB_PORT", "5432")),
                DB_NAME=os.environ.get("FAMILY_DB_NAME", "family_db"),
                DB_SCHEMA=os.environ.get("FAMILY_DB_SCHEMA", os.environ.get("FAMILY_AMI_USER", "memory")),
                DB_ADMIN_USER=os.environ.get("FAMILY_ADMIN_USER", "postgres"),
                DB_ADMIN_PASSWORD=os.environ.get("FAMILY_ADMIN_PASSWORD", ""),
                DB_ECHO_SQL=os.environ.get("FAMILY_ENABLE_TRANSACTION_LOGGING", "false").lower() in ("true", "yes", "1"),
                EMBEDDING_MODEL=os.environ.get("FAMILY_VECTOR_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            )
        else:
            # Используем стандартную загрузку конфигурации
            _global_config = load_config(config_file, env_prefix)
    
    return _global_config