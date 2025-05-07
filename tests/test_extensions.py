import pytest
from datetime import date
from app.core.extensions import (
    load_extension_fields,
    get_extension_field,
    validate_extension_value,
    get_namespace_fields
)

def test_load_extension_fields():
    """Test loading extension fields from YAML."""
    fields = load_extension_fields()
    assert len(fields.fields) > 0
    assert any(f.name == "external_id" for f in fields.fields)
    assert any(f.name == "mrn" for f in fields.fields)

def test_get_extension_field():
    """Test getting a specific extension field."""
    field = get_extension_field("external_id", "epic")
    assert field is not None
    assert field.name == "external_id"
    assert field.namespace == "epic"
    assert field.type == "string"
    assert field.required is True

def test_validate_extension_value():
    """Test validating extension field values."""
    field = get_extension_field("external_id", "epic")
    
    # Valid value
    assert validate_extension_value(field, "ABC12345") is True
    
    # Invalid value (wrong pattern)
    assert validate_extension_value(field, "abc12345") is False
    
    # Invalid value (wrong length)
    assert validate_extension_value(field, "ABC123") is False
    
    # Required field with None value
    assert validate_extension_value(field, None) is False
    
    # Test boolean field
    field = get_extension_field("is_active", "cerner")
    assert validate_extension_value(field, True) is True
    assert validate_extension_value(field, False) is True
    assert validate_extension_value(field, "true") is False

def test_get_namespace_fields():
    """Test getting all fields for a namespace."""
    epic_fields = get_namespace_fields("epic")
    assert len(epic_fields) > 0
    assert all(f.namespace == "epic" for f in epic_fields)
    
    cerner_fields = get_namespace_fields("cerner")
    assert len(cerner_fields) > 0
    assert all(f.namespace == "cerner" for f in cerner_fields) 