"""
Управление сессиями базы данных.

Модуль предоставляет функции для создания и управления сессиями SQLAlchemy,
включая различные уровни изоляции транзакций.
"""

from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine import Engine
from sqlalchemy import text


def create_session_factory(engine: Engine):
    """
    Создает фабрику сессий SQLAlchemy.
    
    Args:
        engine (Engine): SQLAlchemy Engine
        
    Returns:
        scoped_session: Фабрика сессий SQLAlchemy
    """
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)


@contextmanager
def session_scope(session_factory):
    """
    Контекстный менеджер для работы с сессией БД.
    
    Автоматически создает сессию, выполняет коммит при успешном
    выполнении или откат при возникновении исключения, и закрывает
    сессию в конце работы.
    
    Args:
        session_factory: Фабрика сессий SQLAlchemy
        
    Yields:
        Session: Активная сессия SQLAlchemy
    
    Example:
        with session_scope(session_factory) as session:
            # выполнение операций с сессией
            session.add(some_object)
    """
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_isolated_session(session_factory, isolation_level="SERIALIZABLE"):
    """
    Создает сессию с заданным уровнем изоляции транзакций.
    
    Важно: эта функция не только создает сессию, но и настраивает
    соединение с нужным уровнем изоляции до начала транзакции.
    
    Args:
        session_factory: Фабрика сессий SQLAlchemy
        isolation_level (str): Уровень изоляции (READ UNCOMMITTED, 
                              READ COMMITTED, REPEATABLE READ, SERIALIZABLE)
            
    Returns:
        Session: Сессия с установленным уровнем изоляции
    """
    session = session_factory()
    
    # Закрываем автоматически начатую транзакцию
    if session.is_active:
        session.commit()
    
    # Устанавливаем уровень изоляции для всей сессии
    session.execute(text(f"SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL {isolation_level}"))
    
    return session


@contextmanager
def isolated_session_scope(session_factory, isolation_level="SERIALIZABLE"):
    """
    Контекстный менеджер для работы с изолированной сессией.
    
    Создает сессию с заданным уровнем изоляции и управляет её жизненным циклом.
    
    Args:
        session_factory: Фабрика сессий SQLAlchemy
        isolation_level (str): Уровень изоляции транзакций
            
    Yields:
        Session: Активная сессия с установленным уровнем изоляции
    
    Example:
        with isolated_session_scope(session_factory, "SERIALIZABLE") as session:
            # выполнение операций в изолированной сессии
            session.add(some_object)
    """
    session = create_isolated_session(session_factory, isolation_level)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def begin_nested_transaction(session):
    """
    Начинает вложенную транзакцию (SAVEPOINT) в текущей сессии.
    
    Args:
        session: Сессия SQLAlchemy
        
    Returns:
        NestedTransaction: Объект вложенной транзакции
        
    Example:
        nested = begin_nested_transaction(session)
        try:
            # операции в рамках вложенной транзакции
            nested.commit()
        except:
            nested.rollback()
    """
    return session.begin_nested()


def refresh_transaction_view(session):
    """
    Обновляет представление сессии о текущем состоянии базы данных.
    
    Эта функция гарантирует, что сессия увидит последние изменения,
    сделанные в других сессиях. Для этого она завершает текущую
    транзакцию и начинает новую.
    
    Args:
        session: Сессия SQLAlchemy
        
    Returns:
        Session: Та же сессия с обновленным представлением
    
    Example:
        # После изменений в другой сессии
        refresh_transaction_view(session)
        # Теперь эта сессия видит последние изменения
    """
    if session.is_active:
        session.commit()
    session.begin()
    return session


def ensure_isolated_transactions(session1, session2):
    """
    Обеспечивает гарантированную изоляцию между двумя сессиями.
    
    Эта функция настраивает две сессии таким образом, чтобы они
    работали с максимальной изоляцией друг от друга. Это особенно
    полезно для тестирования и критических операций, где требуется
    гарантированная независимость транзакций.
    
    Args:
        session1: Первая сессия SQLAlchemy
        session2: Вторая сессия SQLAlchemy
        
    Returns:
        tuple: (session1, session2) - настроенные сессии
    """
    # Закрываем текущие транзакции, если они есть
    if session1.in_transaction():
        session1.commit()
    if session2.in_transaction():
        session2.commit()
    
    # Устанавливаем максимальный уровень изоляции для обеих сессий
    session1.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
    session2.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
    
    # Запросы будут автоматически начинать новые транзакции с заданным уровнем изоляции
    
    return session1, session2