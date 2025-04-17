"""
Common fixtures for testing AMI memory subsystem.
"""

import os
import pytest
import tempfile
import dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, clear_mappers

from undermaind.core.base import Base, create_base
from undermaind.models import setup_relationships
from undermaind.utils.db_init import DatabaseInitializer
from undermaind.utils.ami_init import AmiInitializer


# Load test configuration from test_config.env
test_config_path = os.path.join(os.path.dirname(__file__), 'test_config.env')
dotenv.load_dotenv(test_config_path)


@pytest.fixture(scope="session")
def db_config():
    """Configuration for test database."""
    ami_user = os.environ.get("FAMILY_AMI_USER", "ami_test_user")
    return {
        "DB_NAME": os.environ.get("FAMILY_DB_NAME", "family_db"),
        "DB_USER": ami_user,
        "DB_SCHEMA": ami_user,  # Use AMI name as schema name
        "DB_PASSWORD": os.environ.get("FAMILY_AMI_PASSWORD", "ami_secure_password"),
        "DB_HOST": os.environ.get("FAMILY_DB_HOST", "localhost"),
        "DB_PORT": os.environ.get("FAMILY_DB_PORT", "5432"),
        "DB_ADMIN_USER": os.environ.get("FAMILY_ADMIN_USER", "family_admin"),
        "DB_ADMIN_PASSWORD": os.environ.get("FAMILY_ADMIN_PASSWORD", "Cold68#Fire"),
    }


@pytest.fixture(scope="session", autouse=True)
def setup_base_model_schema(db_config):
    """
    Initializes the base model with the correct schema for tests.
    This fixture is automatically applied to all tests in the session.
    """
    # Save original metadata
    original_metadata = Base.metadata
    original_schema = original_metadata.schema
    
    # Set the correct schema for tests
    Base.metadata.schema = db_config["DB_SCHEMA"]
    
    yield
    
    # Restore original schema after tests
    Base.metadata.schema = original_schema


@pytest.fixture(scope="session")
def test_engine_memory():
    """Creates SQLite in-memory database for fast tests without PostgreSQL."""
    engine = create_engine('sqlite:///:memory:')
    
    @event.listens_for(engine, "connect")
    def do_connect(dbapi_connection, connection_record):
        # Enable foreign key support for SQLite
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Set relationships
    setup_relationships()
    
    yield engine
    
    # Drop all tables and clear mappers
    Base.metadata.drop_all(engine)
    clear_mappers()


@pytest.fixture(scope="session")
def test_db_initializer(db_config):
    """Creates database initializer for tests."""
    return DatabaseInitializer(
        db_host=db_config["DB_HOST"],
        db_port=int(db_config["DB_PORT"]),
        db_name=db_config["DB_NAME"],
        admin_user=db_config["DB_ADMIN_USER"],
        admin_password=db_config["DB_ADMIN_PASSWORD"]
    )


@pytest.fixture(scope="session")
def test_ami_initializer(test_db_initializer, db_config):
    """Creates AMI initializer for tests."""
    return AmiInitializer(
        ami_name=db_config["DB_SCHEMA"],
        ami_password=db_config["DB_PASSWORD"],
        db_host=test_db_initializer.db_host,
        db_port=test_db_initializer.db_port,
        db_name=test_db_initializer.db_name,
        admin_user=test_db_initializer.admin_user,
        admin_password=test_db_initializer.admin_password
    )


@pytest.fixture(scope="module")
def test_engine_postgres(db_config, test_db_initializer, test_ami_initializer):
    """
    Creates PostgreSQL database for integration tests.
    Uses DatabaseInitializer and AmiInitializer for correct initialization.
    """
    # Initialize database, recreating it for purity of tests
    test_db_initializer.initialize_database(recreate=True)
    
    # Recreate test AMI instance
    test_ami_initializer.recreate_ami(force=True)
    
    # Use schema directly from configuration
    ami_schema = db_config['DB_SCHEMA']
    
    # Create connection to database with AMI schema specified
    connection_string = (
        f"postgresql://{db_config['DB_USER']}:{db_config['DB_PASSWORD']}@"
        f"{db_config['DB_HOST']}:{db_config['DB_PORT']}/"
        f"{db_config['DB_NAME']}"
    )
    engine = create_engine(connection_string)
    
    # Set search path
    with engine.connect() as conn:
        conn.execute(text(f"SET search_path TO {ami_schema}, public"))
    
    # Set relationships
    setup_relationships()
    
    yield engine
    
    # Cleanup: drop test AMI instance
    test_ami_initializer.drop_ami(force=True)


@pytest.fixture(scope="function")
def db_session_memory(test_engine_memory):
    """Creates session for working with test database in memory."""
    Session = sessionmaker(bind=test_engine_memory)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()
    
    # Clear all tables after each test
    for table in reversed(Base.metadata.sorted_tables):
        test_engine_memory.execute(table.delete())


@pytest.fixture(scope="function")
def db_session_postgres(test_engine_postgres, db_config):
    """Creates session for working with test database PostgreSQL."""
    Session = sessionmaker(bind=test_engine_postgres)
    session = Session()
    
    # Use schema directly from configuration
    ami_schema = db_config['DB_SCHEMA']
    session.execute(text(f"SET search_path TO {ami_schema}, public"))
    
    yield session
    
    session.rollback()
    session.close()


def pytest_configure(config):
    """Registration of custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marker for integration tests requiring PostgreSQL"
    )