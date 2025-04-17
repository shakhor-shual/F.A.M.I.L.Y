"""
Tests for the base module models/base.py.

Checks the correctness of importing the base class from core/base.py
and its configuration for using the ami_memory schema.
"""

import pytest
from sqlalchemy import inspect
import os
import dotenv

from undermaind.models.base import Base as ModelsBase
from undermaind.core.base import Base as CoreBase

# Load test configuration
test_config_path = os.path.join(os.path.dirname(__file__), 'test_config.env')
dotenv.load_dotenv(test_config_path)

def test_base_import_from_core():
    """Checks that Base in models/base.py is the same object as in core/base.py."""
    # Verify that both base class objects are identical
    assert ModelsBase is CoreBase, "Base in models/base.py must be imported from core/base.py"


def test_models_base_schema():
    """Checks that the schema in Base from models is correctly set up."""
    # Get expected schema name from configuration
    expected_schema = os.environ.get("FAMILY_AMI_USER", "ami_test_user")
    
    # Check schema in metadata
    assert ModelsBase.metadata.schema == expected_schema, f"Database should use schema {expected_schema}"
    
    # Check for naming convention constraints
    naming_convention = ModelsBase.metadata.naming_convention
    assert naming_convention is not None, "Database must have naming conventions"
    assert 'pk' in naming_convention, "Naming convention for primary key is missing"
    assert 'fk' in naming_convention, "Naming convention for foreign key is missing"
    assert 'ix' in naming_convention, "Naming convention for index is missing"
    assert 'uq' in naming_convention, "Naming convention for unique constraint is missing"
    assert 'ck' in naming_convention, "Naming convention for check constraint is missing"


def test_models_base_export():
    """Checks correct export of Base from models/base.py."""
    # Import to verify that Base is available through this import
    from undermaind.models import Base as ImportedBase
    
    # Verify that imported Base is identical to the original
    assert ImportedBase is ModelsBase, "Base must be correctly exported from models/__init__.py"
    assert ImportedBase is CoreBase, "Base must be identical to the base class from core"


def test_setup_relationships_function():
    """
    Checks the existence and functionality of the setup_relationships function.
    
    This function must exist for centralized definition of relationships
    between models.
    """
    from undermaind.models import setup_relationships
    
    # Verify that the function exists and is callable
    assert callable(setup_relationships), "setup_relationships must be a function"