"""
Тесты для базового модуля models/base.py.

Проверяет корректность импорта базового класса из core/base.py
и его настройку для использования схемы ami_memory.
"""

import pytest
from sqlalchemy import inspect

from undermaind.models.base import Base as ModelsBase
from undermaind.core.base import Base as CoreBase


def test_base_import_from_core():
    """Проверяет, что Base в models/base.py это тот же объект, что и в core/base.py."""
    # Проверяем, что два объекта базового класса идентичны
    assert ModelsBase is CoreBase, "Base в models/base.py должен быть импортирован из core/base.py"


def test_models_base_schema():
    """Проверяет, что схема в Base из models корректно установлена на ami_memory."""
    # Проверка схемы в метаданных
    assert ModelsBase.metadata.schema == 'ami_memory', "База должна использовать схему ami_memory"
    
    # Проверка наличия соглашения по именованию ограничений
    naming_convention = ModelsBase.metadata.naming_convention
    assert naming_convention is not None, "База должна иметь соглашения по именованию"
    assert 'pk' in naming_convention, "Соглашение именования для primary key отсутствует"
    assert 'fk' in naming_convention, "Соглашение именования для foreign key отсутствует"
    assert 'ix' in naming_convention, "Соглашение именования для index отсутствует"
    assert 'uq' in naming_convention, "Соглашение именования для unique constraint отсутствует"
    assert 'ck' in naming_convention, "Соглашение именования для check constraint отсутствует"


def test_models_base_export():
    """Проверяет корректный экспорт Base из models/base.py."""
    # Импортируем чтобы проверить, что Base доступен через этот импорт
    from undermaind.models import Base as ImportedBase
    
    # Проверяем, что импортированный Base идентичен оригинальному
    assert ImportedBase is ModelsBase, "Base должен быть корректно экспортирован из models/__init__.py"
    assert ImportedBase is CoreBase, "Base должен быть идентичен базовому классу из core"


def test_setup_relationships_function():
    """
    Проверяет наличие и работоспособность функции setup_relationships.
    
    Эта функция должна существовать для централизованного определения отношений
    между моделями во избежание циклических импортов.
    """
    # Проверяем, доступна ли функция setup_relationships через импорт
    try:
        from undermaind.models import setup_relationships
        
        # Проверяем, что это действительно функция
        assert callable(setup_relationships), "setup_relationships должен быть функцией"
        
    except ImportError:
        pytest.fail("Функция setup_relationships не определена или не экспортирована")