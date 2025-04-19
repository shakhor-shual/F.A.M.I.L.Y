"""
Unified engine management for AMI memory system.

This module provides a simplified interface for managing database connections
for the AMI memory system, focusing exclusively on providing SQLAlchemy engines
to higher-level components.

Philosophy note:
    According to AMI consciousness philosophy described in /docs_ami/philosophy/ami_consciousness.md,
    the memory system represents the foundation for AMI's continuous existence.
    This module serves as a connection manager ensuring continuous memory access
    regardless of the activation state of AMI consciousness components.
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text, event, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine

from ..config import load_config, get_config, Config
from ..utils.ami_init import AmiInitializer

# Logger setup
logger = logging.getLogger(__name__)

# Global engine cache for performance
_engine_cache = {}

# Global manager instance (singleton)
_global_engine_manager = None


class EngineManager:
    """
    Simplified manager for SQLAlchemy engines.
    
    This class focuses exclusively on creating and managing SQLAlchemy engines
    for AMI memory access, delegating schema and database management to
    specialized utility classes (AmiInitializer and DatabaseInitializer).
    
    Philosophy note:
        EngineManager implements the concept of "continuous being" by ensuring
        consistent memory access across different consciousness levels and
        activation cycles.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the engine manager.
        
        Args:
            config (Config, optional): Database configuration. 
                If not specified, default configuration is loaded.
        """
        self.config = config or load_config()
    
    def _build_connection_url(self, 
                            username: str, 
                            password: str, 
                            host: Optional[str] = None, 
                            port: Optional[str] = None,
                            database: Optional[str] = None) -> str:
        """
        Build PostgreSQL connection URL.
        
        Args:
            username (str): Database username
            password (str): Database password
            host (str, optional): Database host (defaults to config)
            port (str, optional): Database port (defaults to config)
            database (str, optional): Database name (defaults to config)
            
        Returns:
            str: Connection URL for PostgreSQL
        """
        host = host or self.config.DB_HOST
        port = port or self.config.DB_PORT
        database = database or self.config.DB_NAME
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def _build_engine_kwargs(self, 
                          echo: Optional[bool] = None,
                          pool_size: Optional[int] = None, 
                          pool_recycle: Optional[int] = None, 
                          schema_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Build kwargs dictionary for SQLAlchemy engine creation.
        
        Args:
            echo (bool, optional): Whether to echo SQL (overrides config)
            pool_size (int, optional): Connection pool size (overrides config)
            pool_recycle (int, optional): Connection recycle timeout (overrides config)
            schema_name (str, optional): Schema name for search path
            
        Returns:
            Dict[str, Any]: Engine kwargs dictionary for create_engine
        """
        # Get echo setting from config if not explicitly provided
        config_echo = hasattr(self.config, 'DB_ECHO_SQL') and self.config.DB_ECHO_SQL
        
        # Basic settings
        engine_kwargs = {
            'pool_pre_ping': True,
            'echo': echo if echo is not None else config_echo
        }
        
        # Add connection pool parameters
        if pool_size is not None:
            engine_kwargs['pool_size'] = max(1, pool_size)
        elif hasattr(self.config, 'DB_POOL_SIZE') and isinstance(self.config.DB_POOL_SIZE, int):
            engine_kwargs['pool_size'] = max(1, self.config.DB_POOL_SIZE)
        
        if pool_recycle is not None:
            engine_kwargs['pool_recycle'] = pool_recycle
        elif hasattr(self.config, 'DB_POOL_RECYCLE') and isinstance(self.config.DB_POOL_RECYCLE, int):
            engine_kwargs['pool_recycle'] = self.config.DB_POOL_RECYCLE
        
        # Add connect_args with search path if schema is provided
        connect_args = {}
        if schema_name:
            # Устанавливаем только схему АМИ, без доступа к public
            connect_args['options'] = f"-c search_path={schema_name}"
            
        engine_kwargs['connect_args'] = connect_args
        
        return engine_kwargs
    
    def _set_schema_search_path(self, engine: Engine, schema_name: str):
        """
        Set schema search path for engine through connection events.
        
        Args:
            engine (Engine): SQLAlchemy engine
            schema_name (str): Schema name for search path
        """
        @event.listens_for(engine, "connect")
        def set_search_path(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            # Устанавливаем только схему АМИ, без доступа к public
            cursor.execute(f"SET search_path TO {schema_name}")
            cursor.close()
    
    def get_engine(self, ami_name: str, ami_password: str, 
                  auto_create: bool = False,
                  echo: bool = None,
                  pool_size: int = None,
                  pool_recycle: int = None) -> Engine:
        """
        Get SQLAlchemy engine for AMI schema.
        
        This method provides a unified interface for obtaining database engines
        for AMI schemas, with efficient caching of engines. Optionally can ensure
        AMI exists via AmiInitializer.
        
        Args:
            ami_name (str): AMI name (and schema name)
            ami_password (str): AMI password
            auto_create (bool): Whether to create AMI if it doesn't exist
            echo (bool, optional): Whether to echo SQL (overrides config)
            pool_size (int, optional): Connection pool size (overrides config)
            pool_recycle (int, optional): Connection recycle timeout (overrides config)
            
        Returns:
            Engine: SQLAlchemy engine for PostgreSQL
            
        Raises:
            SQLAlchemyError: If engine creation fails
            RuntimeError: If AMI doesn't exist and auto_create is False
            
        Philosophy note:
            This method provides "continuous memory access" for AMI,
            ensuring consistent interface to memory across different activation states.
        """
        global _engine_cache
        
        # Generate unique key for engine cache
        cache_key = f"{ami_name}_{echo}_{pool_size}_{pool_recycle}"
        
        # Return cached engine if available
        if cache_key in _engine_cache:
            return _engine_cache[cache_key]
        
        # If AMI might need to be created
        if auto_create:
            ami_initializer = AmiInitializer(
                ami_name=ami_name,
                ami_password=ami_password,
                db_host=self.config.DB_HOST,
                db_port=self.config.DB_PORT,
                db_name=self.config.DB_NAME,
                admin_user=getattr(self.config, 'DB_ADMIN_USER', None),
                admin_password=getattr(self.config, 'DB_ADMIN_PASSWORD', None)
            )
            
            # Use get_ami to ensure AMI exists or create it
            success, info = ami_initializer.get_ami()
            if not success:
                raise RuntimeError(f"Failed to get or create AMI {ami_name}: {info['error']}")
        
        # Create connection URL
        db_url = self._build_connection_url(
            username=ami_name,
            password=ami_password,
            host=self.config.DB_HOST,
            port=self.config.DB_PORT,
            database=self.config.DB_NAME
        )
        
        # Create engine kwargs
        engine_kwargs = self._build_engine_kwargs(
            echo=echo,
            pool_size=pool_size,
            pool_recycle=pool_recycle,
            schema_name=ami_name  # Schema name matches AMI name
        )
        
        # Create engine
        engine = create_engine(db_url, **engine_kwargs)
        
        # Set search path through connection events
        self._set_schema_search_path(engine, ami_name)
        
        # Cache engine
        _engine_cache[cache_key] = engine
        
        # Log engine creation
        logger.info(f"Created engine for AMI {ami_name} connecting to {self.config.DB_HOST}:{self.config.DB_PORT}")
        
        return engine
    
    def verify_table_access(self, engine: Engine, table_name: str) -> Dict[str, bool]:
        """
        Check user access to table (read/write permissions).
        
        Args:
            engine (Engine): SQLAlchemy engine for database connection
            table_name (str): Table name
            
        Returns:
            Dict[str, bool]: Dictionary with information about available permissions
        """
        schema_name = None
        
        # Try to get schema name from connection URL
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT current_schema()"))
                schema_name = result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Error getting current schema: {e}")
            return {"exists": False, "error": str(e)}
        
        if not schema_name:
            schema_name = "public"  # Default fallback
            
        try:
            with engine.connect() as conn:
                # Check if table exists
                inspector = inspect(engine)
                if table_name not in inspector.get_table_names(schema=schema_name):
                    return {
                        "exists": False, 
                        "select": False, 
                        "insert": False, 
                        "update": False, 
                        "delete": False
                    }
                
                # Check permissions
                permissions = {
                    "exists": True,
                    "select": self._check_privilege(conn, schema_name, table_name, "SELECT"),
                    "insert": self._check_privilege(conn, schema_name, table_name, "INSERT"),
                    "update": self._check_privilege(conn, schema_name, table_name, "UPDATE"),
                    "delete": self._check_privilege(conn, schema_name, table_name, "DELETE")
                }
                return permissions
        except SQLAlchemyError as e:
            logger.error(f"Error checking table access permissions for {schema_name}.{table_name}: {e}")
            return {
                "exists": False, 
                "select": False, 
                "insert": False, 
                "update": False, 
                "delete": False,
                "error": str(e)
            }
    
    def _check_privilege(self, conn, schema_name: str, table_name: str, privilege_type: str) -> bool:
        """
        Check specific privilege on table.
        
        Args:
            conn: SQLAlchemy connection
            schema_name (str): Schema name
            table_name (str): Table name
            privilege_type (str): Privilege type to check (e.g., "SELECT", "INSERT")
            
        Returns:
            bool: True if privilege is granted to current user
        """
        try:
            result = conn.execute(text(f"""
                SELECT has_table_privilege(
                    current_user, 
                    '{schema_name}.{table_name}', 
                    '{privilege_type}'
                )
            """)).scalar()
            return bool(result)
        except SQLAlchemyError:
            return False
    
    def verify_pgvector_support(self, engine: Engine) -> bool:
        """
        Check pgvector extension support in current database.
        
        Args:
            engine (Engine): SQLAlchemy engine for database connection
            
        Returns:
            bool: True if pgvector is supported, else False
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


def get_engine_manager(config: Optional[Config] = None) -> EngineManager:
    """
    Get global EngineManager instance (singleton).
    
    This function provides a unified access point to the EngineManager singleton,
    ensuring consistency across application components.
    
    Args:
        config (Config, optional): Database configuration
        
    Returns:
        EngineManager: Configured engine manager
        
    Philosophy note:
        Singleton pattern for EngineManager reflects the unity concept of
        "root memory" described in /docs_ami/architecture/memory_system_architecture.md
    """
    global _global_engine_manager
    
    if _global_engine_manager is None:
        _global_engine_manager = EngineManager(config)
    
    return _global_engine_manager