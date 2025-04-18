"""
SQLAlchemy engine configuration and creation.

This module provides functions to create and configure SQLAlchemy engine
for working with PostgreSQL and pgvector extension, taking into account the separation
of privileges between administrators (table creation) and regular users (read/write operations).
"""

import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import SQLAlchemyError
from ..config import Config

# Logger setup
logger = logging.getLogger(__name__)

# Global engine instance for use throughout the application
_global_engine = None

def get_engine(config=None, for_admin_tasks=False):
    """
    Returns global SQLAlchemy engine instance or creates a new one if it doesn't exist yet.
    
    Args:
        config (Config, optional): Configuration object. If not specified,
                                  default configuration from config module will be used.
        for_admin_tasks (bool, optional): If True, engine is created for administrative
                                        tasks. Defaults to False.
                                       
    Returns:
        Engine: SQLAlchemy Engine
    """
    global _global_engine
    
    if _global_engine is None or for_admin_tasks:
        # If configuration is not provided, use default settings
        if config is None:
            from ..config import get_config
            config = get_config()
            
        # Create new engine
        _global_engine = create_db_engine(config, for_admin_tasks)
        
        # Log connection information
        engine_info = f"{config.DB_USERNAME}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
        if for_admin_tasks:
            logger.info(f"Created administrative engine: {engine_info}")
        else:
            logger.info(f"Created standard engine: {engine_info}")
    
    return _global_engine


def create_db_engine(config: Config, for_admin_tasks=False):
    """
    Creates and configures SQLAlchemy engine for PostgreSQL+pgvector.
    
    Args:
        config (Config): Configuration object with connection parameters
        for_admin_tasks (bool, optional): If True, engine is created for administrative
                                        tasks (schema and table creation). Defaults to False.
        
    Returns:
        Engine: SQLAlchemy Engine
    """
    connection_url = URL.create(
        drivername='postgresql+psycopg2',
        username=config.DB_USERNAME,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME
    )
    
    # Create explicit parameters for connection pool
    engine_kwargs = {
        'pool_pre_ping': True,
        'echo': config.DB_ECHO_SQL
    }
    
    # Add pool parameters only if they are defined in configuration
    if hasattr(config, 'DB_POOL_SIZE') and isinstance(config.DB_POOL_SIZE, (int)):
        engine_kwargs['pool_size'] = max(1, config.DB_POOL_SIZE)  # Minimum 1 connection
    
    if hasattr(config, 'DB_POOL_RECYCLE') and isinstance(config.DB_POOL_RECYCLE, (int)):
        engine_kwargs['pool_recycle'] = config.DB_POOL_RECYCLE
    
    # Form connection options depending on user type
    if for_admin_tasks:
        # For admin tasks, set a separate pool to avoid
        # conflicts with regular connections
        if 'pool_size' in engine_kwargs:
            # For admin tasks, use a smaller pool
            engine_kwargs['pool_size'] = min(2, engine_kwargs['pool_size'])
        
        # Use connect_args parameter to distinguish admin pool
        connect_args = engine_kwargs.get('connect_args', {})
        connect_args['application_name'] = f"family_admin_{config.DB_USERNAME}"
        engine_kwargs['connect_args'] = connect_args
        
        logger.debug(f"Creating administrative engine for user {config.DB_USERNAME}")
    else:
        # For regular tasks, set default schema
        if hasattr(config, 'DB_SCHEMA') and config.DB_SCHEMA:
            # Add schema name to connection options
            connect_args = engine_kwargs.get('connect_args', {})
            connect_args['options'] = f"-c search_path={config.DB_SCHEMA}"
            engine_kwargs['connect_args'] = connect_args
            
            logger.debug(f"Default schema set: {config.DB_SCHEMA}")
    
    engine = create_engine(
        connection_url,
        **engine_kwargs
    )
    
    return engine


def is_admin_engine(engine):
    """
    Checks if engine has administrative privileges (can create tables).
    
    Args:
        engine: SQLAlchemy Engine to check
        
    Returns:
        bool: True if engine has administrative privileges
    """
    # Check user login
    username = engine.url.username
    # family_admin or other users with name containing admin
    # are considered administrative
    return username == 'family_admin' or 'admin' in username.lower()


def ensure_schema_exists(engine, schema_name):
    """
    Checks if schema exists in database. Does not create schema,
    only verifies its existence.
    
    Args:
        engine: SQLAlchemy Engine for DB connection
        schema_name (str): Schema name to check
        
    Returns:
        bool: True if schema exists
    """
    try:
        inspector = inspect(engine)
        schemas = inspector.get_schema_names()
        return schema_name in schemas
    except SQLAlchemyError as e:
        logger.error(f"Error checking schema existence {schema_name}: {e}")
        return False


def verify_table_access(engine, schema_name, table_name):
    """
    Checks user access to table (read/write permissions).
    
    Args:
        engine: SQLAlchemy Engine for DB connection
        schema_name (str): Schema name
        table_name (str): Table name
        
    Returns:
        dict: Dictionary with information about available permissions (select, insert, update, delete)
    """
    try:
        with engine.connect() as conn:
            # Check table existence
            inspector = inspect(engine)
            if not table_name in inspector.get_table_names(schema=schema_name):
                return {
                    "exists": False, 
                    "select": False, 
                    "insert": False, 
                    "update": False, 
                    "delete": False
                }
            
            # Check SELECT permissions
            try:
                conn.execute(text(f"SELECT 1 FROM {schema_name}.{table_name} LIMIT 0"))
                select_access = True
            except SQLAlchemyError:
                select_access = False
            
            # Check INSERT permissions
            insert_access = False
            try:
                # Use direct query to check INSERT permissions
                result = conn.execute(text(f"""
                    SELECT has_table_privilege(
                        current_user, 
                        '{schema_name}.{table_name}', 
                        'INSERT'
                    )
                """)).scalar()
                insert_access = bool(result)
            except SQLAlchemyError:
                insert_access = False
            
            # Check UPDATE permissions
            update_access = False
            try:
                result = conn.execute(text(f"""
                    SELECT has_table_privilege(
                        current_user, 
                        '{schema_name}.{table_name}', 
                        'UPDATE'
                    )
                """)).scalar()
                update_access = bool(result)
            except SQLAlchemyError:
                update_access = False
            
            # Check DELETE permissions
            delete_access = False
            try:
                result = conn.execute(text(f"""
                    SELECT has_table_privilege(
                        current_user, 
                        '{schema_name}.{table_name}', 
                        'DELETE'
                    )
                """)).scalar()
                delete_access = bool(result)
            except SQLAlchemyError:
                delete_access = False
            
            # Return permission check result
            return {
                "exists": True,
                "select": select_access,
                "insert": insert_access,
                "update": update_access,
                "delete": delete_access
            }
    except SQLAlchemyError as e:
        logger.error(f"Error checking table access permissions {schema_name}.{table_name}: {e}")
        return {
            "exists": False, 
            "select": False, 
            "insert": False, 
            "update": False, 
            "delete": False,
            "error": str(e)
        }


def verify_pgvector_support(engine):
    """
    Checks pgvector extension support in current database.
    
    Args:
        engine: SQLAlchemy Engine for DB connection
        
    Returns:
        bool: True if pgvector is supported
    """
    try:
        with engine.connect() as conn:
            # Check for vector extension
            result = conn.execute(text(
                "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
            )).scalar()
            
            return result > 0
    except SQLAlchemyError:
        return False


def grant_table_access(admin_engine, schema_name, table_name, user_name, 
                      grant_select=True, grant_insert=True, 
                      grant_update=True, grant_delete=True):
    """
    Grants table access permissions to a user.
    Should only be called with an administrative engine.
    
    Args:
        admin_engine: SQLAlchemy Engine with administrative privileges
        schema_name (str): Schema name
        table_name (str): Table name
        user_name (str): Username to grant permissions to
        grant_select (bool): Grant SELECT permission
        grant_insert (bool): Grant INSERT permission
        grant_update (bool): Grant UPDATE permission
        grant_delete (bool): Grant DELETE permission
        
    Returns:
        bool: True if permissions were granted successfully
    """
    # Check that engine has administrative privileges
    if not is_admin_engine(admin_engine):
        logger.error("Attempt to grant permissions with non-administrative engine")
        return False
    
    try:
        with admin_engine.connect() as conn:
            permissions = []
            if grant_select:
                permissions.append("SELECT")
            if grant_insert:
                permissions.append("INSERT")
            if grant_update:
                permissions.append("UPDATE")
            if grant_delete:
                permissions.append("DELETE")
                
            if not permissions:
                logger.warning("No permissions specified to grant")
                return False
                
            permissions_str = ", ".join(permissions)
            
            # Grant table permissions
            conn.execute(text(f"""
                GRANT {permissions_str} ON {schema_name}.{table_name} TO {user_name}
            """))
            conn.commit()
            
            logger.info(f"Permissions {permissions_str} on table {schema_name}.{table_name} granted to user {user_name}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error granting access permissions: {e}")
        return False