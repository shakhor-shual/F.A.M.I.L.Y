"""
Модуль моделей памяти АМИ (Artificial Mind Identity) для проекта F.A.M.I.L.Y.
Этот модуль экспортирует все модели данных и предоставляет функцию для настройки отношений.
"""

from sqlalchemy.orm import relationship

from .base import Base
from .consciousness import (
    Participant,
    MemoryContext, 
    Experience,
    ThoughtChain,
    InformationResource,
    ExperienceConnection,
    setup_consciousness_relationships
)


def setup_relationships():
    """
    Настраивает все отношения между моделями данных.
    Эта функция должна вызываться после импорта всех моделей и до начала
    работы с базой данных.
    """
    # Настройка отношений для сознательного уровня
    setup_consciousness_relationships()
    
    # В будущем здесь будет настройка отношений других уровней памяти
    # setup_subconsciousness_relationships()
    # setup_deep_level_relationships()
    # setup_metasystem_relationships()


# Экспортируем все модели и функции для удобного импорта
__all__ = [
    # Базовый класс
    'Base',
    
    # Сознательный уровень
    'Participant',
    'MemoryContext',
    'Experience',
    'ThoughtChain',
    'InformationResource',
    'ExperienceConnection',
    
    # Функция настройки отношений
    'setup_relationships'
]