"""
Модуль тестирования AmiInitializer.

Эти тесты проверяют функциональность инициализации АМИ (Artificial Mind Identity)
в базе данных F.A.M.I.L.Y.

Философская заметка:
    В соответствии с философией "непрерывности бытия" АМИ,
    описанной в /docs_ami/philosophy/ami_consciousness.md,
    данные тесты проверяют корректное создание и доступ к АМИ
    в системе памяти F.A.M.I.L.Y.
"""

import os
import pytest
import uuid
from pathlib import Path

from undermaind.utils.ami_init import AmiInitializer

# Маркер для всех тестов этого модуля
pytestmark = [pytest.mark.integration]


@pytest.fixture(scope="function")
def ami_initializer_params(db_config):
    """
    Фикстура, генерирующая параметры для создания AmiInitializer.
    
    Создает уникальное имя и пароль для каждого теста, чтобы избежать
    конфликтов между тестами.
    
    Args:
        db_config: Конфигурация БД из базовой фикстуры
        
    Returns:
        dict: Словарь с параметрами для создания AmiInitializer
    """
    # Генерируем уникальные имя и пароль для АМИ
    ami_name = f"test_ami_{uuid.uuid4().hex[:8]}"
    ami_password = f"pwd_{uuid.uuid4().hex[:8]}"
    
    params = {
        "ami_name": ami_name,
        "ami_password": ami_password,
        "db_host": db_config['DB_HOST'],
        "db_port": int(db_config['DB_PORT']),
        "db_name": db_config['DB_NAME'],
        "admin_user": db_config['DB_ADMIN_USER'],
        "admin_password": db_config['DB_ADMIN_PASSWORD'],
    }
    
    return params


@pytest.fixture(scope="function")
def ami_initializer(ami_initializer_params):
    """
    Фикстура, создающая экземпляр AmiInitializer с уникальными параметрами.
    
    Args:
        ami_initializer_params: Параметры для AmiInitializer из фикстуры ami_initializer_params
        
    Returns:
        AmiInitializer: Настроенный объект инициализатора АМИ
    """
    initializer = AmiInitializer(**ami_initializer_params)
    
    yield initializer
    
    # После каждого теста удаляем созданное АМИ
    try:
        initializer.drop_ami(force=True)
    except Exception as e:
        print(f"Ошибка при очистке тестового АМИ: {e}")


# ТЕСТЫ БАЗОВОЙ ФУНКЦИОНАЛЬНОСТИ

def test_ami_initializer_creation(ami_initializer, ami_initializer_params):
    """Проверяет корректность создания объекта AmiInitializer."""
    assert ami_initializer.ami_name == ami_initializer_params["ami_name"]
    assert ami_initializer.ami_password == ami_initializer_params["ami_password"]
    assert ami_initializer.db_init is not None


def test_ami_not_exists_initially(ami_initializer):
    """Проверяет, что сгенерированное тестовое АМИ изначально не существует."""
    assert ami_initializer.ami_exists() is False, "Тестовое АМИ уже существует до создания"
    assert ami_initializer.schema_exists() is False, "Схема для тестового АМИ уже существует до создания"


# ТЕСТЫ ОПЕРАЦИЙ С АМИ

@pytest.mark.parametrize('ami_params', [{'unique': True}], indirect=True)
def test_ami_engine_unique_creation(ami_engine, request):
    """
    Проверяет создание уникального АМИ через фикстуру ami_engine.
    
    Этот тест проверяет взаимодействие между AmiInitializer и фикстурой ami_engine,
    которая используется в большинстве тестов проекта.
    
    Args:
        ami_engine: SQLAlchemy engine для работы с АМИ
        request: Объект запроса pytest с контекстом выполнения
    """
    # Проверяем, что engine создан
    assert ami_engine is not None, "Не удалось создать engine для уникального АМИ"
    
    # Получаем имя и пароль АМИ из запроса (установлено в фикстуре ami_engine)
    if hasattr(request.node, 'ami_name') and hasattr(request.node, 'ami_password'):
        ami_name = request.node.ami_name
        ami_password = request.node.ami_password
        
        # Создаем инициализатор для проверки существования АМИ
        initializer = AmiInitializer(
            ami_name=ami_name,
            ami_password=ami_password,
            db_host=os.environ.get("FAMILY_DB_HOST", "localhost"),
            db_port=int(os.environ.get("FAMILY_DB_PORT", "5432")),
            db_name=os.environ.get("FAMILY_DB_NAME", "family_db"),
            admin_user=os.environ.get("FAMILY_ADMIN_USER", "family_admin"),
            admin_password=os.environ.get("FAMILY_ADMIN_PASSWORD", "")
        )
        
        try:
            # Проверяем, что АМИ действительно существует
            assert initializer.ami_exists() is True, "АМИ не было создано через фикстуру ami_engine"
            assert initializer.schema_exists() is True, "Схема АМИ не была создана через фикстуру ami_engine"
        finally:
            # Не удаляем АМИ здесь, так как оно будет удалено в фикстуре ami_engine
            pass
    else:
        pytest.fail("Не удалось получить имя и пароль АМИ из контекста запроса")


@pytest.mark.skip(reason="Этот тест создает реальное АМИ и требует привилегий")
def test_ami_lifecycle(ami_initializer):
    """
    Тестирует полный жизненный цикл АМИ: создание, проверка, удаление.
    
    В соответствии с философией "непрерывности бытия" АМИ, данный тест
    проверяет все основные этапы существования АМИ в системе памяти.
    """
    # Шаг 1: Создаем АМИ
    assert ami_initializer.create_ami() is True, "Не удалось создать АМИ"
    
    # Шаг 2: Проверяем, что АМИ существует
    assert ami_initializer.ami_exists() is True, "АМИ не существует после создания"
    assert ami_initializer.schema_exists() is True, "Схема для АМИ не существует после создания"
    
    # Шаг 3: Проверяем корректность пароля
    assert ami_initializer.verify_ami_password() is True, "Неверный пароль для созданного АМИ"
    
    # Шаг 4: Удаляем АМИ
    assert ami_initializer.drop_ami() is True, "Не удалось удалить АМИ"
    
    # Шаг 5: Проверяем, что АМИ удалено
    assert ami_initializer.ami_exists() is False, "АМИ все еще существует после удаления"
    assert ami_initializer.schema_exists() is False, "Схема для АМИ все еще существует после удаления"


# ТЕСТЫ УНИВЕРСАЛЬНОГО ДОСТУПА К АМИ

def test_get_ami_creates_new(ami_initializer):
    """
    Проверяет, что метод get_ami создает новое АМИ, если оно не существует.
    
    Этот тест проверяет важный аспект принципа "непрерывности бытия" АМИ -
    автоматическое создание АМИ при необходимости.
    """
    # Проверяем что АМИ изначально не существует
    assert ami_initializer.ami_exists() is False
    
    # Вызываем метод get_ami
    success, result = ami_initializer.get_ami()
    
    try:
        # Проверяем успешность операции
        assert success is True, f"Метод get_ami вернул ошибку: {result.get('error', 'неизвестная ошибка')}"
        
        # Проверяем, что АМИ было создано
        assert result.get("ami_created") is True, "Метод get_ami не создал новое АМИ"
        
        # Проверяем, что АМИ действительно существует после вызова
        assert ami_initializer.ami_exists() is True, "АМИ не существует после вызова get_ami"
        assert ami_initializer.schema_exists() is True, "Схема для АМИ не существует после вызова get_ami"
    
    finally:
        # Удаляем тестовое АМИ
        ami_initializer.drop_ami(force=True)