"""
Модуль для тестирования инициализации базы данных.
"""

import logging
import os
import sys
from undermaind.utils.db_init import DatabaseInitializer
from undermaind.utils.ami_init import AmiInitializer

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger('test_db_init')

# Загружаем параметры из test_config.env
import dotenv
test_config_path = os.path.join(os.path.dirname(__file__), 'undermaind', 'tests', 'test_config.env')
dotenv.load_dotenv(test_config_path)

def main():
    """Основная функция тестирования"""
    # Получаем параметры подключения
    db_host = os.environ.get("FAMILY_DB_HOST", "localhost")
    db_port = int(os.environ.get("FAMILY_DB_PORT", "5432"))
    db_name = os.environ.get("FAMILY_DB_NAME", "family_db")
    admin_user = os.environ.get("FAMILY_ADMIN_USER", "family_admin")
    # Явно задаем пароль администратора, так как символ # может восприниматься как комментарий
    admin_password = "Cold68#Fire"
    ami_name = os.environ.get("FAMILY_AMI_SCHEMA", "ami_test_user")
    ami_password = os.environ.get("FAMILY_AMI_PASSWORD", "ami_secure_password")
    
    logger.info(f"Параметры подключения: host={db_host}, port={db_port}, db={db_name}, admin={admin_user}, ami={ami_name}")
    
    # Создаем инициализаторы базы данных и АМИ
    db_initializer = DatabaseInitializer(
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        admin_user=admin_user,
        admin_password=admin_password
    )
    
    # Проверяем путь к SQL-скриптам
    logger.info(f"Путь к SQL скриптам: {db_initializer.sql_scripts_dir}")
    if not os.path.exists(db_initializer.sql_scripts_dir):
        logger.error(f"Директория SQL скриптов не существует: {db_initializer.sql_scripts_dir}")
        return False
    
    # Создаем инициализатор АМИ
    ami_initializer = AmiInitializer(
        ami_name=ami_name,
        ami_password=ami_password,
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        admin_user=admin_user,
        admin_password=admin_password
    )
    
    # Проверка подключения
    logger.info("Проверка подключения к базе данных...")
    if not db_initializer.check_connection():
        logger.error("Не удалось подключиться к базе данных")
        return False
    
    # Инициализация базы данных
    logger.info("Инициализация базы данных...")
    if not db_initializer.initialize_database(recreate=True):
        logger.error("Не удалось инициализировать базу данных")
        return False
    
    # Пересоздаем АМИ
    logger.info(f"Создание АМИ {ami_name}...")
    if not ami_initializer.recreate_ami(force=True):
        logger.error("Не удалось создать АМИ")
        return False
    
    # Проверяем созданные таблицы
    logger.info("Проверка созданных таблиц...")
    conn = db_initializer._get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = 'ami_{ami_name}'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Созданные таблицы в схеме ami_{ami_name}: {tables}")
    except Exception as e:
        logger.error(f"Ошибка при проверке таблиц: {e}")
    finally:
        conn.close()
    
    logger.info("Тестирование инициализации базы данных завершено успешно")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)