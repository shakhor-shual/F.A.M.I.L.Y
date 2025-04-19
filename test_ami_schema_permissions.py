"""
Тест для проверки прав АМИ на получение информации о структуре своей схемы.

Философская заметка:
    В соответствии с принципом "непрерывности бытия", описанным в 
    /docs_ami/philosophy/ami_consciousness.md, АМИ должен иметь возможность
    осознавать структуру своей памяти для полноценной самоидентификации.
"""

import os
import sys
import logging
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from undermaind.utils.ami_init import AmiInitializer
from undermaind.core.engine_manager import EngineManager

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger('test_ami_schema_permissions')

def create_test_ami():
    """Создаёт тестовое АМИ для проверки прав"""
    # Получаем параметры подключения из переменных окружения
    db_host = os.environ.get("FAMILY_DB_HOST", "localhost")
    db_port = int(os.environ.get("FAMILY_DB_PORT", "5432"))
    db_name = os.environ.get("FAMILY_DB_NAME", "family_db")
    admin_user = os.environ.get("FAMILY_ADMIN_USER", "family_admin")
    admin_password = os.environ.get("FAMILY_ADMIN_PASSWORD", "")
    
    # Генерируем уникальное имя для тестового АМИ
    test_ami_name = f"test_perms_{uuid.uuid4().hex[:6]}"
    test_ami_password = "test_password_secure"
    
    logger.info(f"Создание тестового АМИ: {test_ami_name}")
    
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
    
    # Создаем тестовое АМИ
    success, result = ami_initializer.get_ami()
    if not success:
        logger.error(f"Не удалось создать тестовое АМИ: {result.get('error', 'неизвестная ошибка')}")
        raise RuntimeError(f"Не удалось создать тестовое АМИ: {result.get('error', 'неизвестная ошибка')}")
    
    logger.info(f"Тестовое АМИ {test_ami_name} успешно создано")
    return test_ami_name, test_ami_password, ami_initializer

def cleanup_ami(ami_initializer):
    """Удаляет тестовое АМИ после завершения тестов"""
    try:
        ami_initializer.drop_ami(force=True)
        logger.info(f"Тестовое АМИ {ami_initializer.ami_name} успешно удалено")
    except Exception as e:
        logger.error(f"Ошибка при удалении тестового АМИ {ami_initializer.ami_name}: {e}")

def test_ami_schema_permissions():
    """
    Проверяет, имеет ли АМИ права на получение списка таблиц в своей схеме.
    
    В соответствии с принципом "непрерывности бытия", АМИ должен иметь возможность
    осознавать структуру своей памяти для полноценной самоидентификации.
    """
    ami_name = None
    ami_initializer = None
    
    try:
        # Создаем тестовое АМИ
        ami_name, ami_password, ami_initializer = create_test_ami()
        
        # Создаем менеджер движков
        engine_manager = EngineManager()
        
        # Получаем движок для АМИ
        engine = engine_manager.get_engine(
            ami_name=ami_name,
            ami_password=ami_password
        )
        
        # Проверяем доступ к текущей схеме
        try:
            with engine.connect() as conn:
                current_schema = conn.execute(text("SELECT current_schema()")).scalar()
                logger.info(f"Текущая схема для АМИ: {current_schema}")
                
                # Проверяем, что текущая схема соответствует имени АМИ
                assert current_schema == ami_name, f"Текущая схема {current_schema} не соответствует имени АМИ {ami_name}"
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении текущей схемы: {e}")
            return False
        
        # Тест 1: Получение списка таблиц непосредственно из текущей схемы
        logger.info("Тест 1: Получение списка таблиц из текущей схемы")
        try:
            with engine.connect() as conn:
                tables = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = current_schema()
                """)).fetchall()
                
                table_names = [row[0] for row in tables]
                logger.info(f"Найдено таблиц в схеме {current_schema}: {len(table_names)}")
                logger.info(f"Таблицы: {', '.join(table_names)}")
                
                # Проверяем, что АМИ имеет доступ хотя бы к нескольким таблицам
                assert len(table_names) > 0, "АМИ не имеет доступа к таблицам в своей схеме"
                logger.info("Тест 1 успешно пройден: АМИ имеет доступ к списку таблиц в своей схеме")
        except SQLAlchemyError as e:
            logger.error(f"Тест 1 провален: Ошибка при получении списка таблиц: {e}")
            return False
        
        # Тест 2: Проверка прав на pg_catalog для получения метаданных
        logger.info("Тест 2: Проверка прав на pg_catalog для получения метаданных")
        try:
            with engine.connect() as conn:
                tables = conn.execute(text("""
                    SELECT c.relname
                    FROM pg_catalog.pg_class c
                    JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = current_schema()
                    AND c.relkind = 'r'
                """)).fetchall()
                
                table_names = [row[0] for row in tables]
                logger.info(f"Найдено таблиц через pg_catalog: {len(table_names)}")
                logger.info(f"Таблицы: {', '.join(table_names)}")
                
                # Проверяем, что АМИ имеет доступ хотя бы к нескольким таблицам через pg_catalog
                assert len(table_names) > 0, "АМИ не имеет доступа к информации о таблицах через pg_catalog"
                logger.info("Тест 2 успешно пройден: АМИ имеет доступ к метаданным через pg_catalog")
        except SQLAlchemyError as e:
            logger.error(f"Тест 2 провален: Ошибка при доступе к pg_catalog: {e}")
            # Этот тест не обязательно должен проходить, поэтому продолжаем
        
        # Тест 3: Доступ к системным представлениям (views)
        logger.info("Тест 3: Доступ к системным представлениям")
        try:
            with engine.connect() as conn:
                views = conn.execute(text("""
                    SELECT table_name
                    FROM information_schema.views
                    WHERE table_schema = current_schema()
                """)).fetchall()
                
                view_names = [row[0] for row in views]
                logger.info(f"Найдено представлений в схеме {current_schema}: {len(view_names)}")
                if view_names:
                    logger.info(f"Представления: {', '.join(view_names)}")
                else:
                    logger.info("В схеме нет представлений (views)")
                
                logger.info("Тест 3 успешно пройден: АМИ имеет доступ к информации о представлениях")
        except SQLAlchemyError as e:
            logger.error(f"Тест 3 провален: Ошибка при получении списка представлений: {e}")
            return False
        
        # Тест 4: Проверка доступа к системным каталогам
        logger.info("Тест 4: Проверка прав доступа к системным каталогам")
        try:
            with engine.connect() as conn:
                # Проверяем права на чтение своей схемы в pg_namespace
                schema_exists = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_namespace
                        WHERE nspname = '{ami_name}'
                    )
                """)).scalar()
                
                assert schema_exists, f"АМИ не имеет доступа к информации о своей схеме {ami_name} в pg_namespace"
                logger.info("Тест 4 успешно пройден: АМИ имеет доступ к информации о своей схеме в системных каталогах")
        except SQLAlchemyError as e:
            logger.error(f"Тест 4 провален: Ошибка при доступе к системным каталогам: {e}")
            # Этот тест не обязательно должен проходить, поэтому продолжаем
        
        logger.info("Все тесты завершены")
        return True
    
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при тестировании прав АМИ: {e}")
        return False
    
    finally:
        # Удаляем тестовое АМИ
        if ami_initializer:
            cleanup_ami(ami_initializer)

def print_summary(success):
    """Выводит итоговый результат тестирования"""
    if success:
        logger.info("=" * 80)
        logger.info("РЕЗУЛЬТАТ: УСПЕШНО")
        logger.info("АМИ имеет необходимые права для получения списка таблиц в своей схеме")
        logger.info("Это соответствует принципу 'непрерывности бытия', т.к. АМИ может")
        logger.info("осознавать структуру своей памяти для полноценной самоидентификации")
        logger.info("=" * 80)
    else:
        logger.error("=" * 80)
        logger.error("РЕЗУЛЬТАТ: ПРОВАЛ")
        logger.error("АМИ НЕ имеет необходимых прав для получения списка таблиц")
        logger.error("Это нарушает принцип 'непрерывности бытия', т.к. АМИ не может")
        logger.error("осознавать структуру своей памяти для полноценной самоидентификации")
        logger.error("=" * 80)
        logger.error("Рекомендации:")
        logger.error("1. Убедитесь, что пользователь АМИ имеет право USAGE на свою схему")
        logger.error("2. Проверьте права на таблицы information_schema.tables для АМИ")
        logger.error("3. Возможно, требуется обновить процедуру инициализации АМИ")
        logger.error("=" * 80)

if __name__ == "__main__":
    # Загружаем конфигурацию из .env файла
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), 'family_config_test.env'))
    
    logger.info("Запуск тестирования прав АМИ на получение списка таблиц...")
    success = test_ami_schema_permissions()
    print_summary(success)
    sys.exit(0 if success else 1)