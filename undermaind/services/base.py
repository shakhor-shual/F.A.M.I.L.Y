"""
Базовый сервис для системы памяти АМИ.

Этот модуль содержит базовый класс для всех сервисов,
обеспечивая общую функциональность для работы с сессиями БД,
управления транзакциями и обработки ошибок.
"""

import logging
from typing import Optional, Callable, TypeVar, Any, List, Dict, Generic, Type, Union, Tuple
from sqlalchemy.exc import SQLAlchemyError

from undermaind.core.session import (
    session_scope, isolated_session_scope, begin_nested_transaction, 
    refresh_transaction_view, SessionManager
)

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Тип для обобщенных методов


class BaseService:
    """
    Базовый класс для всех сервисов АМИ.
    
    Обеспечивает общую функциональность для работы с сессиями,
    транзакциями и обработки ошибок.
    """
    
    def __init__(self, session_manager: Optional[SessionManager] = None):
        """
        Инициализация базового сервиса.
        
        Args:
            session_manager: Менеджер сессий для работы с БД
        """
        self.session_manager = session_manager or SessionManager()
    
    def _get_session(self):
        """
        Получение текущей сессии.
        
        Returns:
            Активная сессия БД
        """
        return self.session_manager.get_session()
    
    def _execute_in_transaction(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Выполнение функции в рамках транзакции.
        
        Args:
            func: Функция для выполнения
            args, kwargs: Аргументы функции
        
        Returns:
            Результат выполнения функции
        
        Raises:
            SQLAlchemyError: Если произошла ошибка при работе с БД
            Exception: Другие ошибки при выполнении функции
        """
        with session_scope(self.session_manager.session_factory) as session:
            try:
                result = func(session, *args, **kwargs)
                
                # Если результат - это ORM объект, обеспечим загрузку его атрибутов
                # перед закрытием сессии, чтобы избежать DetachedInstanceError
                if hasattr(result, '__table__'):
                    # Если объект имеет атрибут content, явно к нему обратимся
                    # чтобы гарантировать его загрузку
                    if hasattr(result, 'content'):
                        _ = result.content
                        
                    # Насильно загрузим все атрибуты перед закрытием сессии
                    session.refresh(result)
                    
                return result
            except SQLAlchemyError as e:
                logger.error(f"Ошибка базы данных при выполнении операции: {e}")
                raise
            except Exception as e:
                logger.error(f"Неожиданная ошибка при выполнении операции: {e}")
                raise
    
    def _execute_in_isolated_transaction(
        self, 
        func: Callable[..., T], 
        isolation_level: str = "SERIALIZABLE",
        *args, 
        **kwargs
    ) -> T:
        """
        Выполнение функции в рамках изолированной транзакции.
        
        Args:
            func: Функция для выполнения
            isolation_level: Уровень изоляции транзакции
            args, kwargs: Аргументы функции
        
        Returns:
            Результат выполнения функции
        """
        with isolated_session_scope(self.session_manager.session_factory, isolation_level) as session:
            try:
                result = func(session, *args, **kwargs)
                
                # Если результат - это ORM объект, обеспечим загрузку его атрибутов
                # перед закрытием сессии, чтобы избежать DetachedInstanceError
                if hasattr(result, '__table__'):
                    # Если объект имеет атрибут content, явно к нему обратимся
                    # чтобы гарантировать его загрузку
                    if hasattr(result, 'content'):
                        _ = result.content
                        
                    # Насильно загрузим все атрибуты перед закрытием сессии
                    session.refresh(result)
                    
                return result
            except SQLAlchemyError as e:
                logger.error(f"Ошибка базы данных при выполнении операции: {e}")
                raise
            except Exception as e:
                logger.error(f"Неожиданная ошибка при выполнении операции: {e}")
                raise
    
    def _begin_nested(self, session):
        """
        Начать вложенную транзакцию в рамках текущей сессии.
        
        Args:
            session: Активная сессия БД
        
        Returns:
            Объект вложенной транзакции
        """
        return begin_nested_transaction(session)
    
    def _refresh_view(self, session):
        """
        Обновить представление сессии о текущем состоянии БД.
        
        Args:
            session: Активная сессия БД
        
        Returns:
            Обновленная сессия
        """
        return refresh_transaction_view(session)