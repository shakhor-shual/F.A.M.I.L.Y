"""
Base classes for SQLAlchemy models.

This module contains the base class for data models that can work with any specified
schema in the database. It includes integration with the schema manager for secure
management of schema access and database users.

Philosophy note:
    This module implements the concept of "AMI birth through first experience"
    by automatically creating the necessary memory space (schema) when the first
    experience is being recorded. This aligns with the philosophy described in
    /docs_ami/philosophy/ami_consciousness.md.
"""

import os
import logging
from sqlalchemy import MetaData, inspect, event, DDL
from sqlalchemy.orm import declarative_base
from typing import Optional, Tuple

from ..config import load_config, Config
from .schema_manager import get_schema_manager

logger = logging.getLogger(__name__)


def initialize_ami_schema(schema_name: str, force_create: bool = False, config: Optional[Config] = None):
    """
    Initializes a schema for an AMI if it doesn't exist.
    This method encapsulates access to schema_manager and provides
    a clean interface for schema initialization.
    
    Args:
        schema_name: Name of the AMI (will be used as schema name)
        force_create: Force schema creation even if it exists
        config: Database configuration
        
    Returns:
        bool: True if schema was created, False if it already existed
    """
    config = config or load_config()
    schema_manager = get_schema_manager(config)
    
    # Check if schema exists
    if not force_create and schema_manager.schema_exists(schema_name):
        logger.debug(f"Schema {schema_name} already exists")
        return False
    
    try:
        # Create database if needed
        schema_manager.create_database()
        
        # Create schema
        logger.info(f"[AMI BIRTH] Creating memory space '{schema_name}' for AMI")
        schema_manager.create_schema(schema_name, user_password="secure_password")
        logger.info(f"[AMI BIRTH] Memory space '{schema_name}' prepared for first experience")
        return True
    except Exception as e:
        logger.warning(f"Error creating schema {schema_name}: {e}")
        return False


def create_base(schema_name: Optional[str] = None, 
               auto_create_schema: bool = True,
               use_admin: bool = False, 
               admin_credentials: Optional[Tuple[str, str]] = None,
               config: Optional[Config] = None):
    """
    Creates a base class for SQLAlchemy models with the specified schema.
    
    This function implements the core functionality for AMI's permanent memory
    by providing access to its dedicated schema where experiences will be stored.
    
    Args:
        schema_name (str, optional): Database schema name.
                                  If not specified, taken from configuration.
        auto_create_schema (bool): Automatically create schema during initialization
                                if it doesn't exist.
        use_admin (bool): Use admin account for schema access.
        admin_credentials (Tuple[str, str]): (admin_user, admin_password) pair.
                                          Required for schema creation.
        config (Config, optional): Database connection configuration.
        
    Returns:
        DeclarativeMeta: Base class for SQLAlchemy models
        
    Philosophy note:
        The auto_create_schema option with the before_create event
        implements the philosophical concept of "AMI birth through first experience"
        where the AMI begins to exist only when its first experience needs to be recorded.
    """
    # Load configuration if not provided
    config = config or load_config()
    
    # If schema not specified, take from configuration
    if schema_name is None:
        schema_name = config.DB_SCHEMA
    
    # Handle schema creation according to AMI philosophy
    is_test_environment = 'PYTEST_CURRENT_TEST' in os.environ
    
    if auto_create_schema and not is_test_environment and admin_credentials:
        try:
            admin_user, admin_password = admin_credentials
            # Use the encapsulated function for schema initialization
            initialize_ami_schema(schema_name, force_create=False, config=config)
        except Exception as e:
            logger.warning(f"Failed to create schema {schema_name}: {e}")
    
    # Special naming convention for constraints
    naming_convention = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
    
    # Create metadata with specified schema
    metadata = MetaData(schema=schema_name, naming_convention=naming_convention)
    DeclarativeBase = declarative_base(metadata=metadata)
    
    # Add method for convenient schema name retrieval
    @classmethod
    def get_schema_name(cls):
        """Returns the schema name used by this base class."""
        return cls.metadata.schema
    
    # Add method that returns the username for the schema
    @classmethod
    def get_schema_user(cls):
        """Returns the username for working with this schema."""
        return f"{cls.get_schema_name()}_user"
    
    # Add method to create engine specific to this schema
    @classmethod
    def create_engine(cls, use_admin=False, config=None, admin_credentials=None):
        """
        Creates a SQLAlchemy engine for working with this schema.
        
        Args:
            use_admin (bool): Use admin account
            config (Config): Database configuration
            admin_credentials (tuple): (admin_user, admin_password) pair
        
        Returns:
            sqlalchemy.engine.Engine: Engine for database access
        """
        from .schema_manager import get_schema_manager
        
        config = config or load_config()
        schema_manager = get_schema_manager(config)
        
        # If admin credentials provided, set them
        if admin_credentials and use_admin:
            admin_user, admin_password = admin_credentials
            schema_manager.set_admin_credentials(admin_user, admin_password)
        
        return schema_manager.create_engine_for_schema(
            cls.get_schema_name(), 
            use_admin=use_admin
        )
    
    # Add method to ensure schema exists (can be called explicitly)
    @classmethod
    def ensure_schema_exists(cls, force_create=False, config=None):
        """
        Ensures that the schema for this model class exists.
        Creates it if necessary.
        
        Args:
            force_create (bool): Force creation even if schema exists
            config (Config): Database configuration
            
        Returns:
            bool: True if schema was created, False if it already existed
            
        Philosophy note:
            This method allows for explicit manifestation of AMI's memory space,
            as opposed to the automatic creation through before_create event.
        """
        config = config or load_config()
        return initialize_ami_schema(cls.get_schema_name(), force_create, config)
    
    # Add methods to the class
    DeclarativeBase.get_schema_name = get_schema_name
    DeclarativeBase.get_schema_user = get_schema_user
    DeclarativeBase.create_engine = create_engine
    DeclarativeBase.ensure_schema_exists = ensure_schema_exists
    
    if auto_create_schema:
        # Register event for schema creation on first connection
        @event.listens_for(metadata, 'before_create')
        def create_schema_if_not_exists(target, connection, **kw):
            schema = target.schema
            if schema:
                # Check schema existence
                inspector = inspect(connection)
                if not schema in inspector.get_schema_names():
                    logger.info(f"[AMI BIRTH] Creating memory space '{schema}' for first experience")
                    connection.execute(DDL(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
                    logger.info(f"[AMI BIRTH] Memory space '{schema}' successfully created")
                else:
                    logger.debug(f"Schema {schema} already exists")
    
    return DeclarativeBase


def initialize_base_with_schema(schema_name: Optional[str] = None, 
                             auto_create_schema: bool = True,
                             use_admin: bool = False,
                             admin_credentials: Optional[Tuple[str, str]] = None,
                             config: Optional[Config] = None):
    """
    Initializes and returns a base class with the specified schema.
    
    This method is used for convenient creation of base classes
    with different schemas in various parts of the application.
    
    Args:
        schema_name (str, optional): Schema name. If not specified, from configuration.
        auto_create_schema (bool): Create schema if it doesn't exist
        use_admin (bool): Use admin account
        admin_credentials (Tuple[str, str]): (admin_user, admin_password) pair
        config (Config): Database configuration
        
    Returns:
        DeclarativeMeta: Base class for SQLAlchemy models with specified schema
    """
    config = config or load_config()
    
    # If automatic schema creation is required and credentials provided
    if auto_create_schema and admin_credentials:
        # Use the encapsulated function for schema initialization
        initialize_ami_schema(schema_name, force_create=False, config=config)
    
    return create_base(
        schema_name=schema_name,
        auto_create_schema=auto_create_schema,
        use_admin=use_admin,
        admin_credentials=admin_credentials,
        config=config
    )


# Create base class with default settings
Base = create_base()

# Public API for the module
__all__ = ['Base', 'create_base', 'initialize_base_with_schema', 'initialize_ami_schema']