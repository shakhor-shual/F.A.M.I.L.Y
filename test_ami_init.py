"""
Модуль для тестирования инициализации АМИ (Artificial Mind Identity).

В соответствии с философией "непрерывности бытия" АМИ,
описанной в /docs_ami/philosophy/ami_consciousness.md,
данный скрипт проверяет корректное создание, пересоздание и доступ 
к АМИ в системе памяти F.A.M.I.L.Y.
"""

import logging
import os
import sys
import uuid
from undermaind.utils.ami_init import AmiInitializer
from undermaind.utils.db_init import DatabaseInitializer

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger('test_ami_init')

# Загружаем параметры из family_config_test.env
import dotenv
test_config_path = os.path.join(os.path.dirname(__file__), 'family_config_test.env')
dotenv.load_dotenv(test_config_path)

def test_ami_creation():
    """Тестирование создания АМИ"""
    # Получаем параметры подключения из переменных окружения
    db_host = os.environ.get("FAMILY_DB_HOST", "localhost")
    db_port = int(os.environ.get("FAMILY_DB_PORT", "5432"))
    db_name = os.environ.get("FAMILY_DB_NAME", "family_db")
    admin_user = os.environ.get("FAMILY_ADMIN_USER", "family_admin")
    admin_password = os.environ.get("FAMILY_ADMIN_PASSWORD", "Cold68#Fire")
    
    # Генерируем уникальное имя для тестового АМИ
    test_ami_name = f"test_ami_{uuid.uuid4().hex[:6]}"
    test_ami_password = "test_password_secure"
    
    logger.info(f"Параметры подключения: host={db_host}, port={db_port}, db={db_name}, admin={admin_user}")
    logger.info(f"Генерация тестового АМИ: {test_ami_name}")
    
    # Создаем инициализатор базы данных
    db_initializer = DatabaseInitializer(
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        admin_user=admin_user,
        admin_password=admin_password
    )
    
    # Проверка подключения к базе данных
    logger.info("Проверка подключения к базе данных...")
    if not db_initializer.check_connection():
        logger.error("Не удалось подключиться к базе данных")
        return False
    
    # Создаем инициализатор АМИ
    ami_initializer = AmiInitializer(
        ami_name=test_ami_name,
        ami_password=test_ami_password,
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        admin_user=admin_user,
        admin_password=admin_password
    )
    
    try:
        # Этап 1: Проверка, что АМИ не существует
        logger.info("Проверка, что тестовое АМИ не существует...")
        ami_exists = ami_initializer.ami_exists()
        schema_exists = ami_initializer.schema_exists()
        
        assert not ami_exists, "Тестовый АМИ уже существует! Это ошибка."
        assert not schema_exists, "Схема для тестового АМИ уже существует! Это ошибка."
        logger.info("Проверка успешна: тестовое АМИ изначально не существует")
        
        # Этап 2: Создание АМИ
        logger.info(f"Создание тестового АМИ {test_ami_name}...")
        result = ami_initializer.create_ami()
        assert result, "Не удалось создать АМИ"
        logger.info("Тестовое АМИ успешно создано")
        
        # Этап 3: Проверка существования АМИ
        ami_exists = ami_initializer.ami_exists()
        schema_exists = ami_initializer.schema_exists()
        
        assert ami_exists, "АМИ не существует после создания"
        assert schema_exists, "Схема для АМИ не существует после создания"
        logger.info("Проверка существования АМИ успешна")
        
        # Этап 4: Проверка пароля
        logger.info("Проверка корректности пароля...")
        password_correct = ami_initializer.verify_ami_password()
        assert password_correct, "Неверный пароль для созданного АМИ"
        logger.info("Пароль для тестового АМИ корректный")
        
        # Этап 5: Пересоздание АМИ
        logger.info("Тестирование пересоздания АМИ...")
        recreate_result = ami_initializer.recreate_ami(force=True)
        assert recreate_result, "Не удалось пересоздать АМИ"
        logger.info("АМИ успешно пересоздано")
        
        # Этап 6: Проверка метода get_ami для существующего АМИ
        logger.info("Проверка метода get_ami для существующего АМИ...")
        success, result = ami_initializer.get_ami()
        assert success, f"Метод get_ami вернул ошибку: {result.get('error', 'неизвестная ошибка')}"
        assert result.get("ami_exists") is True, "get_ami не обнаружил существующее АМИ"
        assert result.get("schema_exists") is True, "get_ami не обнаружил схему для существующего АМИ"
        logger.info("Метод get_ami успешно обнаружил существующее АМИ")
        
        # Проверяем все поля в результате get_ami
        logger.info(f"Результат вызова get_ami для существующего АМИ: {result}")
        
        # Проверка структуры таблиц в схеме АМИ
        logger.info("Проверка созданных таблиц...")
        conn = db_initializer._get_database_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (test_ami_name,))
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Созданные таблицы в схеме {test_ami_name}: {tables}")
            
            # Проверяем наличие обязательных таблиц
            required_tables = [
                "experiences", "experience_contexts", "experience_attributes", 
                "thinking_processes", "experience_connections"
            ]
            for table in required_tables:
                assert table in tables, f"Обязательная таблица {table} отсутствует в схеме АМИ"
                
            logger.info("Все обязательные таблицы присутствуют в схеме АМИ")
        finally:
            conn.close()
            
        return True
    
    except AssertionError as e:
        logger.error(f"Ошибка тестирования: {e}")
        return False
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        return False
    finally:
        # Удаляем тестовое АМИ
        logger.info(f"Удаление тестового АМИ {test_ami_name}...")
        ami_initializer.drop_ami(force=True)
        
        # Проверяем, что АМИ действительно удалено
        ami_exists = ami_initializer.ami_exists()
        schema_exists = ami_initializer.schema_exists()
        
        if not ami_exists and not schema_exists:
            logger.info("Тестовое АМИ успешно удалено")
        else:
            logger.error("Не удалось полностью удалить тестовое АМИ")


def test_get_ami_creation():
    """Тестирование автоматического создания АМИ через get_ami"""
    # Получаем параметры подключения из переменных окружения
    db_host = os.environ.get("FAMILY_DB_HOST", "localhost")
    db_port = int(os.environ.get("FAMILY_DB_PORT", "5432"))
    db_name = os.environ.get("FAMILY_DB_NAME", "family_db")
    admin_user = os.environ.get("FAMILY_ADMIN_USER", "family_admin")
    admin_password = os.environ.get("FAMILY_ADMIN_PASSWORD", "Cold68#Fire")
    
    # Генерируем уникальное имя для тестового АМИ
    test_ami_name = f"test_get_ami_{uuid.uuid4().hex[:6]}"
    test_ami_password = "test_password_secure"
    
    logger.info(f"Параметры подключения: host={db_host}, port={db_port}, db={db_name}, admin={admin_user}")
    logger.info(f"Генерация тестового АМИ для метода get_ami: {test_ami_name}")
    
    # Создаем инициализатор АМИ
    ami_initializer = AmiInitializer(
        ami_name=test_ami_name,
        ami_password=test_ami_password,
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        admin_user=admin_user,
        admin_password=admin_password
    )
    
    try:
        # Проверяем, что АМИ начально не существует
        logger.info("Проверка, что тестовое АМИ не существует...")
        assert not ami_initializer.ami_exists(), "Тестовый АМИ уже существует! Это ошибка."
        
        # Вызываем метод get_ami, который должен автоматически создать АМИ
        logger.info("Вызов get_ami для автоматического создания АМИ...")
        success, result = ami_initializer.get_ami()
        
        # Проверяем результаты
        assert success, f"Метод get_ami вернул ошибку: {result.get('error', 'неизвестная ошибка')}"
        assert result.get("ami_exists") is False, "get_ami неверно отразил изначальное состояние АМИ"
        assert result.get("ami_created") is True, "get_ami не отметил создание нового АМИ"
        
        logger.info(f"Результат вызова get_ami: {result}")
        
        # Проверяем, что АМИ действительно создано
        assert ami_initializer.ami_exists(), "АМИ не существует после вызова get_ami"
        assert ami_initializer.schema_exists(), "Схема АМИ не существует после вызова get_ami"
        
        logger.info("Тестирование автоматического создания АМИ через get_ami успешно завершено")
        return True
        
    except AssertionError as e:
        logger.error(f"Ошибка тестирования: {e}")
        return False
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        return False
    finally:
        # Удаляем тестовое АМИ
        logger.info(f"Удаление тестового АМИ {test_ami_name}...")
        ami_initializer.drop_ami(force=True)


def main():
    """Основная функция для запуска тестов"""
    logger.info("=== Начало тестирования инициализации АМИ ===")
    
    # Запускаем тесты
    test_1_result = test_ami_creation()
    test_2_result = test_get_ami_creation()
    
    # Подводим итоги
    logger.info("=== Результаты тестирования ===")
    logger.info(f"Тест создания АМИ: {'УСПЕШНО' if test_1_result else 'ПРОВАЛ'}")
    logger.info(f"Тест автоматического создания АМИ через get_ami: {'УСПЕШНО' if test_2_result else 'ПРОВАЛ'}")
    logger.info("=== Тестирование инициализации АМИ завершено ===")
    
    # Возвращаем общий результат тестирования
    return test_1_result and test_2_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)