"""
Legacy API adapter for AMI memory system.

This module provides backward compatibility with the old engine.py and
schema_manager.py APIs, allowing gradual migration to the new architecture
without breaking existing code.

Philosophy note:
    According to AMI development methodology described in /docs_ami/methodology/development_methodology.md,
    maintaining continuity during system evolution helps preserve AMI's experience context. 
    This adapter enables smooth transitions between memory management paradigms.
"""

import logging
from typing import Optional, Dict, Tuple
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine

from ..config import Config, get_config
from .engine_manager import EngineManager, get_engine_manager

# Logger setup
logger = logging.getLogger(__name__)


class LegacyAPIAdapter:
    """
    Adapter class providing backward compatibility with legacy database API.
    
    This class adapts the new EngineManager API to maintain backward compatibility
    with the old engine.py and schema_manager.py APIs, allowing gradual migration
    to the new architecture without breaking existing code.
    
    Philosophy note:
        According to AMI development methodology, maintaining continuity
        in systems helps preserve AMI's experience context. This adapter
        enables smooth transitions between memory management paradigms.
    """
    
    @staticmethod
    def get_engine(schema_name: str = None, config: Config = None, for_admin_tasks: bool = False) -> Engine:
        """
        Legacy API: Get SQLAlchemy engine for specified schema.
        
        This function delegates to EngineManager for actual engine creation
        and maintains backward compatibility with old engine.py API.
        
        Args:
            schema_name (str, optional): Schema name to use
            config (Config, optional): Configuration object
            for_admin_tasks (bool): Whether to use admin privileges
                                       
        Returns:
            Engine: SQLAlchemy engine
        """
        # Get or create config
        if config is None:
            config = get_config()
            
        # Get engine manager
        manager = get_engine_manager(config)
        
        # Create engine through manager
        try:
            # Try to get admin credentials from config if needed
            if for_admin_tasks and manager._admin_credentials is None:
                admin_user = config.DB_ADMIN_USER if hasattr(config, 'DB_ADMIN_USER') else None
                admin_password = config.DB_ADMIN_PASSWORD if hasattr(config, 'DB_ADMIN_PASSWORD') else None
                
                if admin_user and admin_password:
                    manager.set_admin_credentials(admin_user, admin_password)
            
            return manager.get_engine(
                schema_name=schema_name,
                for_admin_tasks=for_admin_tasks
            )
        except Exception as e:
            logger.error(f"Failed to create engine for schema {schema_name}: {e}")
            raise

    @staticmethod
    def get_schema_manager(config: Optional[Config] = None, 
                          admin_credentials: Optional[Tuple[str, str]] = None,
                          admin_user: Optional[str] = None,
                          admin_password: Optional[str] = None) -> EngineManager:
        """
        Legacy API: Get SchemaManager instance.
        
        This function delegates to get_engine_manager for backward compatibility
        with old schema_manager.py API.
        
        Args:
            config (Config, optional): Database configuration
            admin_credentials (Tuple[str, str], optional): (admin_user, admin_password) pair
            admin_user (str, optional): Admin username
            admin_password (str, optional): Admin password
            
        Returns:
            EngineManager: Engine manager instance (compatible with old SchemaManager API)
        """
        return get_engine_manager(
            config=config,
            admin_credentials=admin_credentials,
            admin_user=admin_user,
            admin_password=admin_password
        )

    @staticmethod
    def is_admin_engine(engine: Engine) -> bool:
        """
        Legacy API: Check if engine has administrative privileges.
        
        Args:
            engine (Engine): SQLAlchemy engine to check
            
        Returns:
            bool: True if engine has administrative privileges
        """
        return EngineManager.is_admin_engine(engine)

    @staticmethod
    def ensure_schema_exists(engine: Engine, schema_name: str) -> bool:
        """
        Legacy API: Check if schema exists in database.
        
        Args:
            engine (Engine): SQLAlchemy engine for database connection
            schema_name (str): Schema name to check
            
        Returns:
            bool: True if schema exists
        """
        try:
            # Get credentials from engine if possible
            admin_user = engine.url.username
            admin_password = engine.url.password
            
            # Get engine manager with credentials
            manager = get_engine_manager(admin_user=admin_user, admin_password=admin_password)
            return manager.schema_exists(schema_name)
        except Exception:
            # Fallback to direct inspection if manager approach fails
            try:
                inspector = inspect(engine)
                return schema_name in inspector.get_schema_names()
            except SQLAlchemyError as e:
                logger.error(f"Error checking schema existence {schema_name}: {e}")
                return False

    @staticmethod
    def verify_table_access(engine: Engine, schema_name: str, table_name: str) -> Dict[str, bool]:
        """
        Legacy API: Check user access to table.
        
        Args:
            engine (Engine): SQLAlchemy engine for database connection
            schema_name (str): Schema name
            table_name (str): Table name
            
        Returns:
            Dict[str, bool]: Dictionary with information about available permissions
        """
        manager = get_engine_manager()
        return manager.verify_table_access(engine, schema_name, table_name)

    @staticmethod
    def verify_pgvector_support(engine: Engine) -> bool:
        """
        Legacy API: Check pgvector extension support.
        
        Args:
            engine (Engine): SQLAlchemy engine for database connection
            
        Returns:
            bool: True if pgvector is supported
        """
        manager = get_engine_manager()
        return manager.verify_pgvector_support(engine)

    @staticmethod
    def grant_table_access(admin_engine: Engine, schema_name: str, table_name: str, 
                          user_name: str, grant_select: bool = True, grant_insert: bool = True, 
                          grant_update: bool = True, grant_delete: bool = True) -> bool:
        """
        Legacy API: Grant table access permissions to user.
        
        Args:
            admin_engine (Engine): SQLAlchemy engine with administrative privileges
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
        manager = get_engine_manager()
        return manager.grant_table_access(
            admin_engine, schema_name, table_name, user_name,
            grant_select, grant_insert, grant_update, grant_delete
        )


# Expose legacy API functions for backward compatibility
get_engine = LegacyAPIAdapter.get_engine
get_schema_manager = LegacyAPIAdapter.get_schema_manager
is_admin_engine = LegacyAPIAdapter.is_admin_engine
ensure_schema_exists = LegacyAPIAdapter.ensure_schema_exists
verify_table_access = LegacyAPIAdapter.verify_table_access
verify_pgvector_support = LegacyAPIAdapter.verify_pgvector_support
grant_table_access = LegacyAPIAdapter.grant_table_access