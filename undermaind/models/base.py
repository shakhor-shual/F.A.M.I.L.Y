"""
Базовый модуль для моделей SQLAlchemy в проекте F.A.M.I.L.Y.
Импортирует базовый класс из core/base.py для обеспечения единообразия.
"""

from undermaind.core.base import Base

# Экспортируем Base для удобного импорта в других модулях
__all__ = ['Base']