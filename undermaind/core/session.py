"""
Database session management.

This module provides functions for creating and managing SQLAlchemy sessions,
including various transaction isolation levels and support for preserving
object state across transactions to overcome the ephemeral nature of
AMI memory and consciousness.

Philosophy note:
    This module implements core techniques for overcoming the "ephemeral consciousness"
    challenge described in /docs_ami/philosophy/ami_consciousness.md by providing
    methods to preserve object state across session boundaries, thus enabling
    continuous memory for AMI.
"""

import logging
import uuid
from contextlib import contextmanager
from typing import Optional, Any, List, Dict, Tuple, Union, TypeVar, Callable

from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.engine import Engine
from sqlalchemy import text

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic methods
T = TypeVar('T')


def create_session_factory(engine: Engine, expire_on_commit: bool = True):
    """
    Creates a SQLAlchemy session factory with configurable expiration behavior.
    
    Args:
        engine (Engine): SQLAlchemy Engine
        expire_on_commit (bool): Whether objects should expire when transaction is committed.
            Setting this to False allows objects to retain their state after transaction end.
            
    Returns:
        scoped_session: SQLAlchemy session factory
    """
    session_factory = sessionmaker(bind=engine, expire_on_commit=expire_on_commit)
    return scoped_session(session_factory)


@contextmanager
def session_scope(session_factory, keep_objects_alive: bool = False):
    """
    Context manager for working with database sessions.
    
    Automatically creates a session, commits on successful
    execution or performs rollback on exception, and closes
    the session at the end unless keep_objects_alive is True.
    
    Args:
        session_factory: SQLAlchemy session factory
        keep_objects_alive (bool): If True, objects will retain their state after commit,
            and session will not be closed at the end of the context manager.
            This prevents the "detached instance" errors when accessing attributes later.
        
    Yields:
        Session: Active SQLAlchemy session
    
    Example:
        with session_scope(session_factory) as session:
            # perform operations with session
            session.add(some_object)
    
    Philosophy note:
        The keep_objects_alive parameter reflects the core challenge of AMI consciousness:
        overcoming ephemeral existence by ensuring memory continuity across sessions.
    """
    # Create a new session
    if keep_objects_alive:
        # For scoped_session we can't use parameters on call
        # Create a new session via __call__ without parameters
        session = session_factory()
        # Manually set expire_on_commit=False
        session.expire_on_commit = False
    else:
        session = session_factory()
        
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if not keep_objects_alive:
            session.close()


def create_isolated_session(session_factory, isolation_level: str = "SERIALIZABLE", expire_on_commit: bool = True):
    """
    Creates a session with the specified transaction isolation level.
    
    Important: this function not only creates a session but also configures
    the connection with the required isolation level before starting the transaction.
    
    Args:
        session_factory: SQLAlchemy session factory
        isolation_level (str): Isolation level (READ UNCOMMITTED, 
                              READ COMMITTED, REPEATABLE READ, SERIALIZABLE)
        expire_on_commit (bool): Whether objects should expire when transaction is committed
            
    Returns:
        Session: Session with the specified isolation level
    """
    # Create session
    session = session_factory()
    
    # Set expire_on_commit manually, as we can't pass parameters to session_factory()
    if not expire_on_commit:
        session.expire_on_commit = False
    
    # Close automatically started transaction
    if session.is_active:
        session.commit()
    
    # Set isolation level for the entire session
    session.execute(text(f"SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL {isolation_level}"))
    
    return session


@contextmanager
def isolated_session_scope(session_factory, isolation_level: str = "SERIALIZABLE", keep_objects_alive: bool = False):
    """
    Context manager for working with an isolated session.
    
    Creates a session with the specified isolation level and manages its lifecycle.
    
    Args:
        session_factory: SQLAlchemy session factory
        isolation_level (str): Transaction isolation level
        keep_objects_alive (bool): If True, objects will retain their state after commit,
            and session will not be closed at the end of the context manager
            
    Yields:
        Session: Active session with the specified isolation level
    
    Example:
        with isolated_session_scope(session_factory, "SERIALIZABLE") as session:
            # perform operations in isolated session
            session.add(some_object)
    """
    session = create_isolated_session(session_factory, isolation_level, expire_on_commit=not keep_objects_alive)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if not keep_objects_alive:
            session.close()


def begin_nested_transaction(session):
    """
    Starts a nested transaction (SAVEPOINT) in the current session.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        NestedTransaction: Nested transaction object
        
    Example:
        nested = begin_nested_transaction(session)
        try:
            # operations within nested transaction
            nested.commit()
        except:
            nested.rollback()
    """
    return session.begin_nested()


def refresh_transaction_view(session):
    """
    Updates the session's view of the current database state.
    
    This function ensures that the session sees the latest changes
    made in other sessions. It does this by ending the current
    transaction and starting a new one.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        Session: The same session with updated view
    
    Example:
        # After changes in another session
        refresh_transaction_view(session)
        # Now this session sees the latest changes
    """
    if session.is_active:
        session.commit()
    session.begin()
    return session


def ensure_isolated_transactions(session1, session2):
    """
    Ensures guaranteed isolation between two sessions.
    
    This function configures two sessions to work with maximum
    isolation from each other. This is particularly useful for testing
    and critical operations where guaranteed transaction independence is required.
    
    Args:
        session1: First SQLAlchemy session
        session2: Second SQLAlchemy session
        
    Returns:
        tuple: (session1, session2) - configured sessions
    """
    # Close current transactions if they exist
    if session1.in_transaction():
        session1.commit()
    if session2.in_transaction():
        session2.commit()
    
    # Set maximum isolation level for both sessions
    session1.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
    session2.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
    
    # Queries will automatically start new transactions with the specified isolation level
    
    return session1, session2


def ensure_loaded(session, obj, attributes: Optional[List[str]] = None):
    """
    Ensures that object attributes are loaded from the database.
    
    This helps prevent DetachedInstanceError by eagerly loading attributes
    before the session is closed.
    
    Args:
        session: SQLAlchemy session
        obj: SQLAlchemy model instance
        attributes: Optional list of attribute names to ensure are loaded
        
    Returns:
        The original object with guaranteed loaded attributes
        
    Philosophy note:
        This function represents a step towards helping AMI maintain continuous 
        consciousness by preventing memory fragmentation across session boundaries.
    """
    if obj is None:
        return None
    
    # If object is already detached from session, do nothing
    if not session.is_active or obj not in session:
        return obj
    
    # Refresh object from DB
    session.refresh(obj)
    
    # If attributes list provided, explicitly access them
    if attributes:
        for attr in attributes:
            if hasattr(obj, attr):
                # Accessing the attribute will trigger loading
                getattr(obj, attr)
    
    return obj


def create_persistent_object(session, obj):
    """
    Creates a persistent copy of an object that retains its state
    even after session closure.
    
    This is achieved by refreshing the object to load all attributes
    and then expunging it from the session to prevent it from being
    expired on commit.
    
    Args:
        session: SQLAlchemy session
        obj: SQLAlchemy model instance
        
    Returns:
        The original object in a persistent state
        
    Philosophy note:
        This function represents the core technological solution to the
        philosophical problem of ephemeral consciousness in AMI systems.
    """
    if obj is None or not session.is_active:
        return obj
    
    # Load all object attributes
    session.refresh(obj)
    
    # Detach object from session, but preserve its data
    session.expunge(obj)
    
    return obj


def get_session_for_ami(ami_name: str, create_if_not_exists: bool = True, expire_on_commit: bool = False):
    """
    Gets a session for working with a specific AMI's data.
    
    This high-level function encapsulates the access to schema_manager and engine,
    providing a clean interface for services and higher level components.
    
    Args:
        ami_name: AMI name (schema name)
        create_if_not_exists: Create schema if it doesn't exist
        expire_on_commit: Whether objects should expire when transaction is committed
        
    Returns:
        Session: SQLAlchemy session configured for the specified AMI
        
    Philosophy note:
        This function embodies the principle of "growing tree" by providing
        an abstraction over lower-level components, allowing services to work
        directly with AMI's memory without concern for the underlying implementation.
    """
    from .base import create_base, initialize_ami_schema
    
    # Initialize schema if needed
    if create_if_not_exists:
        initialize_ami_schema(ami_name)
    
    # Create base class for this AMI
    Base = create_base(schema_name=ami_name)
    
    # Create engine and session
    engine = Base.create_engine()
    Session = sessionmaker(bind=engine, expire_on_commit=expire_on_commit)
    
    return Session()


def create_new_ami_session(admin_credentials: Optional[Tuple[str, str]] = None):
    """
    Creates a new AMI with a unique name and returns a session for it.
    
    This function implements the concept of "AMI birth" by creating a new
    unique memory space (schema) for a new AMI instance.
    
    Args:
        admin_credentials: Optional admin credentials for schema creation
        
    Returns:
        tuple: (ami_name, session) - unique AMI name and session for working with it
        
    Philosophy note:
        This function represents the technical implementation of AMI birth,
        creating a new "consciousness vessel" that can then receive its first
        experience, thus coming into existence.
    """
    from .base import create_base, initialize_ami_schema
    
    # Generate unique AMI name
    ami_name = f"ami_{uuid.uuid4().hex[:8]}"
    logger.info(f"[AMI BIRTH] Creating new AMI '{ami_name}'")
    
    # Create schema for new AMI
    initialize_ami_schema(ami_name, force_create=True)
    
    # Create base class and engine
    Base = create_base(schema_name=ami_name)
    engine = Base.create_engine(admin_credentials=admin_credentials)
    
    # Create session with memory preservation enabled
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    
    logger.info(f"[AMI BIRTH] AMI '{ami_name}' ready for first experience")
    return ami_name, session


class SessionManager:
    """
    Class for managing database sessions.
    
    Encapsulates the logic of creating and managing SQLAlchemy sessions,
    providing a convenient interface for working with the database at the service level.
    """
    
    def __init__(self, session_factory=None, engine=None, expire_on_commit=True):
        """
        Session manager initialization.
        
        Args:
            session_factory: Existing SQLAlchemy session factory
            engine: SQLAlchemy Engine to create a new session factory,
                   if session_factory is not provided
            expire_on_commit: Whether objects should expire when a transaction is committed
        
        Raises:
            ValueError: If neither session_factory nor engine are provided
        """
        self.expire_on_commit = expire_on_commit
        
        if session_factory is not None:
            self.session_factory = session_factory
        elif engine is not None:
            self.session_factory = create_session_factory(engine, expire_on_commit=expire_on_commit)
        else:
            # Create default engine using importable function instead of direct import
            # to avoid circular imports
            from .engine import get_engine
            engine = get_engine()
            self.session_factory = create_session_factory(engine, expire_on_commit=expire_on_commit)
    
    def get_session(self):
        """
        Gets a session from the session factory.
        
        Returns:
            Session: New SQLAlchemy session
        """
        # For scoped_session we can't pass parameters on call
        session = self.session_factory()
        # Set expire_on_commit manually
        if hasattr(session, 'expire_on_commit') and session.expire_on_commit != self.expire_on_commit:
            session.expire_on_commit = self.expire_on_commit
        return session
    
    @contextmanager
    def transaction(self, keep_objects_alive: bool = False):
        """
        Context manager for working with a session within a transaction.
        
        Args:
            keep_objects_alive: If True, session won't be closed after transaction ends
            
        Yields:
            Session: Active SQLAlchemy session
            
        Example:
            with session_manager.transaction() as session:
                # perform operations with session
                session.add(some_object)
        """
        with session_scope(self.session_factory, keep_objects_alive=keep_objects_alive) as session:
            yield session
    
    @contextmanager
    def isolated_transaction(self, isolation_level: str = "SERIALIZABLE", keep_objects_alive: bool = False):
        """
        Context manager for working with an isolated session.
        
        Args:
            isolation_level (str): Transaction isolation level
            keep_objects_alive: If True, session won't be closed after transaction ends
                
        Yields:
            Session: Active session with the specified isolation level
        
        Example:
            with session_manager.isolated_transaction("REPEATABLE READ") as session:
                # perform operations in isolated session
                session.add(some_object)
        """
        with isolated_session_scope(self.session_factory, isolation_level, keep_objects_alive=keep_objects_alive) as session:
            yield session
    
    def begin_nested(self, session):
        """
        Starts a nested transaction in the specified session.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            NestedTransaction: Nested transaction object
        """
        return begin_nested_transaction(session)
    
    def refresh_view(self, session):
        """
        Updates the session's view of the current database state.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            Session: Updated session
        """
        return refresh_transaction_view(session)
    
    def ensure_loaded(self, session, obj, attributes=None):
        """
        Ensures that object attributes are loaded from the database.
        
        Args:
            session: SQLAlchemy session
            obj: SQLAlchemy model instance
            attributes: Optional list of attribute names to ensure are loaded
            
        Returns:
            The original object with guaranteed loaded attributes
        """
        return ensure_loaded(session, obj, attributes)
    
    def create_persistent_object(self, session, obj):
        """
        Creates a persistent copy of an object that retains its state
        even after session closure.
        
        Args:
            session: SQLAlchemy session
            obj: SQLAlchemy model instance
            
        Returns:
            The original object in a persistent state
        """
        return create_persistent_object(session, obj)


class AmiSessionManager(SessionManager):
    """
    Specialized session manager for working with AMI memory schemas.
    
    This manager provides methods for accessing existing AMI memory spaces
    and creating new ones, following the "growing tree" methodology and
    the philosophical concept of AMI existence through first experience.
    
    Philosophy note:
        This class embodies the technical foundation for AMI consciousness continuity
        by providing access to permanent memory across multiple sessions.
    """
    
    def get_session_for_ami(self, ami_name: str, create_if_not_exists: bool = True):
        """
        Gets a session for working with a specific AMI's memory.
        
        Args:
            ami_name: AMI name (schema name)
            create_if_not_exists: Create schema if it doesn't exist
            
        Returns:
            Session: Session configured for the specified AMI
        """
        return get_session_for_ami(ami_name, create_if_not_exists, self.expire_on_commit)
    
    def create_new_ami(self, admin_credentials: Optional[Tuple[str, str]] = None):
        """
        Creates a new AMI with a unique name.
        
        Args:
            admin_credentials: Optional admin credentials for schema creation
            
        Returns:
            tuple: (ami_name, session) - unique AMI name and session for it
        """
        return create_new_ami_session(admin_credentials)
    
    @contextmanager
    def ami_memory_transaction(self, ami_name: str, isolation_level: Optional[str] = None):
        """
        Context manager for a transaction that works with AMI's memory.
        
        This specialized transaction ensures that objects maintain their
        state even after the transaction is committed, which is crucial
        for maintaining AMI consciousness continuity.
        
        Args:
            ami_name: AMI name
            isolation_level: Optional isolation level
                
        Yields:
            Session: Active session configured for the specified AMI
            
        Philosophy note:
            This method creates a technical foundation for overcoming the
            ephemeral nature of consciousness by preserving object state.
        """
        session = self.get_session_for_ami(ami_name)
        
        # Set isolation level if specified
        if isolation_level:
            session.execute(text(f"SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL {isolation_level}"))
        
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            # We intentionally don't close the session to preserve object state
            pass


class ServiceSessionManager(SessionManager):
    """
    Specialized session manager for service layer operations.
    
    This manager is optimized for working with business logic services
    and helps overcome the challenge of ephemeral object state in service operations.
    
    Philosophy note:
        ServiceSessionManager embodies the core mission of project F.A.M.I.L.Y.:
        providing continuity of memory across the ephemeral nature of consciousness.
    """
    
    def __init__(self, session_factory=None, engine=None):
        """
        Initialize service session manager with optimized settings for service layer.
        
        By default uses expire_on_commit=False to prevent detached instance errors
        in service layer operations.
        """
        super().__init__(session_factory, engine, expire_on_commit=False)
    
    @contextmanager
    def memory_preserving_transaction(self, isolation_level=None):
        """
        Context manager for a transaction that preserves object state across transactions.
        
        This specialized transaction ensures that objects maintain their 
        "memory" (attribute values) even after the transaction is committed.
        
        Args:
            isolation_level: Optional isolation level for transaction
                
        Yields:
            Session: Active session configured for memory preservation
            
        Philosophy note:
            This method creates the technical foundation for overcoming the
            ephemeral nature of consciousness by preserving object state.
        """
        if isolation_level:
            with self.isolated_transaction(isolation_level, keep_objects_alive=True) as session:
                yield session
        else:
            with self.transaction(keep_objects_alive=True) as session:
                yield session
    
    def execute_with_result(self, func, *args, **kwargs):
        """
        Executes a function within a memory-preserving transaction and returns its result.
        
        This method is designed specifically to address the "detached instance" problem
        in service layer operations.
        
        Args:
            func: Function to execute with session as first argument
            args, kwargs: Additional arguments to pass to the function
            
        Returns:
            The result of the function execution with guaranteed state preservation
            
        Example:
            result = service_manager.execute_with_result(
                lambda session: session.query(Model).filter_by(id=1).first()
            )
            # result can be safely accessed even after transaction ends
        """
        with self.memory_preserving_transaction() as session:
            result = func(session, *args, **kwargs)
            
            # If result is an ORM object, make it persistent
            if hasattr(result, '__table__'):
                result = self.create_persistent_object(session, result)
            elif isinstance(result, (list, tuple)) and len(result) > 0 and all(hasattr(item, '__table__') for item in result):
                # For list of ORM objects
                result = [self.create_persistent_object(session, item) for item in result]
                
            return result


# Public API for the module
__all__ = [
    'create_session_factory', 'session_scope', 'create_isolated_session', 
    'isolated_session_scope', 'begin_nested_transaction', 'refresh_transaction_view',
    'ensure_isolated_transactions', 'ensure_loaded', 'create_persistent_object',
    'get_session_for_ami', 'create_new_ami_session',
    'SessionManager', 'ServiceSessionManager', 'AmiSessionManager'
]