"""
Интеграционные тесты для BaseService.

Проверяет базовую функциональность сервисного слоя,
работу с транзакциями, сессиями и обработку ошибок.
"""

import pytest
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import MagicMock, patch

from undermaind.services.base import BaseService
from undermaind.core.session import SessionManager
from undermaind.models.consciousness import Experience


@pytest.mark.integration
class TestBaseService:
    """Тесты для базового сервиса."""
    
    def test_init(self):
        """Проверка инициализации базового сервиса."""
        # Создание сервиса с собственным менеджером сессий
        custom_manager = SessionManager()
        service = BaseService(session_manager=custom_manager)
        assert service.session_manager == custom_manager, "Сервис должен использовать переданный менеджер сессий"
        
        # Создание сервиса без менеджера сессий (по умолчанию)
        default_service = BaseService()
        assert default_service.session_manager is not None, "Сервис должен создать менеджер сессий по умолчанию"
    
    def test_get_session(self):
        """Проверка получения сессии из менеджера."""
        # Создаем мок менеджера сессий
        mock_manager = MagicMock()
        mock_session = MagicMock()
        mock_manager.get_session.return_value = mock_session
        
        # Создаем сервис с мок-менеджером
        service = BaseService(session_manager=mock_manager)
        
        # Проверяем получение сессии
        session = service._get_session()
        assert session == mock_session, "Метод должен вернуть сессию из менеджера"
        mock_manager.get_session.assert_called_once(), "Метод должен вызвать get_session у менеджера"
    
    def test_execute_in_transaction_success(self, db_session_postgres):
        """Проверка выполнения операции в транзакции (успешный случай)."""
        # Создаем временную функцию для теста
        def test_func(session, arg1, kwarg1=None):
            # Создаем тестовую запись в БД
            exp = Experience(
                content=f"Test content: {arg1}, {kwarg1}",
                information_category=Experience.CATEGORY_SELF,
                experience_type=Experience.TYPE_THOUGHT,
                subjective_position=Experience.POSITION_REFLECTIVE
            )
            session.add(exp)
            session.flush()
            return exp
        
        # Создаем сервис
        service = BaseService()
        
        # Выполняем функцию в транзакции
        result = service._execute_in_transaction(test_func, "arg_value", kwarg1="kwarg_value")
        
        # Проверяем результат
        assert result is not None, "Функция должна вернуть результат"
        assert isinstance(result, Experience), "Результат должен быть экземпляром Experience"
        assert result.content == "Test content: arg_value, kwarg_value", "Содержимое должно соответствовать параметрам"
        
        # Проверяем, что запись сохранена в БД
        saved_exp = db_session_postgres.query(Experience).filter_by(id=result.id).first()
        assert saved_exp is not None, "Запись должна быть сохранена в БД"
    
    def test_execute_in_transaction_error(self):
        """Проверка обработки ошибки при выполнении операции в транзакции."""
        # Создаем временную функцию, которая вызывает ошибку
        def test_func_error(session, *args, **kwargs):
            raise SQLAlchemyError("Test database error")
        
        # Создаем сервис
        service = BaseService()
        
        # Проверяем, что ошибка пробрасывается
        with pytest.raises(SQLAlchemyError) as excinfo:
            service._execute_in_transaction(test_func_error)
        
        assert "Test database error" in str(excinfo.value), "Должна пробрасываться ошибка SQLAlchemyError"
    
    def test_execute_in_isolated_transaction(self, db_session_postgres):
        """Проверка выполнения операции в изолированной транзакции."""
        # Создаем временную функцию для теста
        def test_func(session, arg1):
            # Создаем тестовую запись в БД
            exp = Experience(
                content=f"Test isolated transaction: {arg1}",
                information_category=Experience.CATEGORY_SELF,
                experience_type=Experience.TYPE_THOUGHT,
                subjective_position=Experience.POSITION_REFLECTIVE
            )
            session.add(exp)
            session.flush()
            return exp
        
        # Создаем сервис
        service = BaseService()
        
        # Выполняем функцию в изолированной транзакции
        result = service._execute_in_isolated_transaction(test_func, isolation_level="SERIALIZABLE", arg1="test_value")
        
        # Проверяем результат
        assert result is not None, "Функция должна вернуть результат"
        assert isinstance(result, Experience), "Результат должен быть экземпляром Experience"
        assert result.content == "Test isolated transaction: test_value", "Содержимое должно соответствовать параметрам"
        
        # Проверяем, что запись сохранена в БД
        saved_exp = db_session_postgres.query(Experience).filter_by(id=result.id).first()
        assert saved_exp is not None, "Запись должна быть сохранена в БД"
    
    def test_begin_nested(self):
        """Проверка создания вложенной транзакции."""
        # Создаем мок сессии
        mock_session = MagicMock()
        
        # Подменяем функцию begin_nested_transaction
        with patch('undermaind.services.base.begin_nested_transaction') as mock_begin_nested:
            mock_nested = MagicMock()
            mock_begin_nested.return_value = mock_nested
            
            # Создаем сервис и вызываем метод
            service = BaseService()
            result = service._begin_nested(mock_session)
            
            # Проверяем, что функция была вызвана с правильными параметрами
            mock_begin_nested.assert_called_once_with(mock_session)
            assert result == mock_nested, "Метод должен вернуть результат вызова begin_nested_transaction"
    
    def test_refresh_view(self):
        """Проверка обновления представления сессии."""
        # Создаем мок сессии
        mock_session = MagicMock()
        
        # Подменяем функцию refresh_transaction_view
        with patch('undermaind.services.base.refresh_transaction_view') as mock_refresh:
            mock_refresh.return_value = mock_session
            
            # Создаем сервис и вызываем метод
            service = BaseService()
            result = service._refresh_view(mock_session)
            
            # Проверяем, что функция была вызвана с правильными параметрами
            mock_refresh.assert_called_once_with(mock_session)
            assert result == mock_session, "Метод должен вернуть обновленную сессию"