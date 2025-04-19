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
        db_host (str): Хост базы данных
        db_port (int): Порт базы данных
        db_name (str): Имя базы данных
        admin_user (str): Имя пользователя с правами администратора БД
        admin_password (str): Пароль пользователя-администратора
        ami_name (str): Имя пользователя AMI
        ami_password (str): Пароль для AMI
        schema (str): Схема базы данных для хранения памяти АМИ
        pool_size (int): Размер пула соединений
        pool_recycle (int): Время (в секундах) для переиспользования соединений в пуле
        echo_sql (bool): Флаг вывода SQL-запросов в лог
        embedding_model (str): Идентификатор модели для создания векторов
    """
    db_host: str
    db_port: int
    db_name: str
    admin_user: str
    admin_password: str
    ami_name: str
    ami_password: str
    schema: str
    pool_size: int = 5
    pool_recycle: int = 3600  # 1 час по умолчанию
    echo_sql: bool = False
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"


def load_config(config_file: Optional[str] = None, env_prefix: str = "FAMILY_") -> Config:
    """
    Загружает конфигурацию из файла и/или переменных окружения.

    Args:
        config_file: Путь к файлу конфигурации (опционально)
        env_prefix: Префикс для переменных окружения (по умолчанию "FAMILY_")

    Returns:
        Config: Объект конфигурации
    """
    # Значения по умолчанию
    config_values = {
        "db_host": "localhost",
        "db_port": 5432,
        "db_name": "family_db",
        "admin_user": "postgres",
        "admin_password": "",
        "ami_name": "ami_user",
        "ami_password": "",
        "schema": "memory",
        "pool_size": 5,
        "pool_recycle": 3600,  # 1 час по умолчанию
        "echo_sql": False,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    }

    # Загрузка из файла, если указан
    if config_file and os.path.exists(config_file):
        with open(config_file, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env_key = f"{env_prefix}{key.upper()}"
                    if env_key in config_values:
                        # Преобразование типов
                        if key in ["db_port", "pool_size", "pool_recycle"]:
                            config_values[env_key] = int(value)
                        elif key == "echo_sql":
                            config_values[env_key] = value.lower() in ("true", "yes", "1")
                        else:
                            config_values[env_key] = value

    # Переопределение значениями из переменных окружения
    for key in config_values.keys():
        env_var = f"{env_prefix}{key.upper()}"
        if env_var in os.environ:
            value = os.environ[env_var]
            if key in ["db_port", "pool_size", "pool_recycle"]:
                config_values[key] = int(value)
            elif key == "echo_sql":
                config_values[key] = value.lower() in ("true", "yes", "1")
            else:
                config_values[key] = value

    # Создание объекта конфигурации
    return Config(**config_values)


# Сохраняем глобальный объект конфигурации для кеширования
_global_config = None

def get_config(config_file: Optional[str] = None, env_prefix: str = "FAMILY_", reload: bool = False) -> Config:
    """
    Получает конфигурацию, используя кешированный объект или загружая конфигурацию заново.
    
    Args:
        config_file: Путь к файлу конфигурации (опционально)
        env_prefix: Префикс для переменных окружения (по умолчанию "FAMILY_")
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
                db_host=os.environ.get("FAMILY_DB_HOST", "localhost"),
                db_port=int(os.environ.get("FAMILY_DB_PORT", "5432")),
                db_name=os.environ.get("FAMILY_DB_NAME", "family_db"),
                admin_user=os.environ.get("FAMILY_ADMIN_USER", "postgres"),
                admin_password=os.environ.get("FAMILY_ADMIN_PASSWORD", ""),
                ami_name=os.environ.get("FAMILY_AMI_USER", "ami_user"),
                ami_password=os.environ.get("FAMILY_AMI_PASSWORD", ""),
                schema=os.environ.get("FAMILY_DB_SCHEMA", "memory"),
                echo_sql=os.environ.get("FAMILY_ENABLE_TRANSACTION_LOGGING", "false").lower() in ("true", "yes", "1"),
                embedding_model=os.environ.get("FAMILY_VECTOR_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            )
        else:
            # Используем стандартную загрузку конфигурации
            _global_config = load_config(config_file, env_prefix)
    
    return _global_config