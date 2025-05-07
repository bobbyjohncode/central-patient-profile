import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import date
import re

class ValidationRule(BaseModel):
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    enum: Optional[List[str]] = None

class ExtensionField(BaseModel):
    name: str
    type: str
    namespace: str
    description: str
    required: bool = False
    validation: Optional[ValidationRule] = None

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['string', 'number', 'boolean', 'date']
        if v not in valid_types:
            raise ValueError(f'Type must be one of {valid_types}')
        return v

class ExtensionFields(BaseModel):
    fields: List[ExtensionField]

def load_extension_fields(yaml_path: str = "app/schemas/extension_fields.yaml") -> ExtensionFields:
    """Load extension fields from YAML file."""
    yaml_file = Path(yaml_path)
    if not yaml_file.exists():
        raise FileNotFoundError(f"Extension fields YAML file not found: {yaml_path}")
    
    with open(yaml_file) as f:
        data = yaml.safe_load(f)
    
    return ExtensionFields(**data)

def get_extension_field(field_name: str, namespace: str) -> Optional[ExtensionField]:
    """Get a specific extension field by name and namespace."""
    fields = load_extension_fields()
    for field in fields.fields:
        if field.name == field_name and field.namespace == namespace:
            return field
    return None

def validate_extension_value(field: ExtensionField, value: Any) -> bool:
    """Validate a value against the field's validation rules."""
    if value is None:
        return not field.required
    
    # Type validation
    if field.type == 'string' and not isinstance(value, str):
        return False
    elif field.type == 'number' and not isinstance(value, (int, float)):
        return False
    elif field.type == 'boolean' and not isinstance(value, bool):
        return False
    elif field.type == 'date':
        if isinstance(value, str):
            try:
                # Try to parse the date string
                date.fromisoformat(value)
                return True
            except ValueError:
                return False
        elif not isinstance(value, date):
            return False
    
    # Validation rules
    if field.validation:
        if field.validation.pattern and not re.match(field.validation.pattern, str(value)):
            return False
        if field.validation.min_length and len(str(value)) < field.validation.min_length:
            return False
        if field.validation.max_length and len(str(value)) > field.validation.max_length:
            return False
        if field.validation.enum and value not in field.validation.enum:
            return False
    
    return True

def get_namespace_fields(namespace: str) -> List[ExtensionField]:
    """Get all extension fields for a specific namespace."""
    fields = load_extension_fields()
    return [field for field in fields.fields if field.namespace == namespace]

def validate_extensions(extensions: Dict[str, Any]) -> None:
    """Validate extension fields against their definitions."""
    if not extensions:
        return

    fields = load_extension_fields()
    for namespace, fields_dict in extensions.items():
        # Get all fields for this namespace
        namespace_fields = {f.name: f for f in fields.fields if f.namespace == namespace}
        
        # Check if all required fields are present
        for field_name, field in namespace_fields.items():
            if field.required and field_name not in fields_dict:
                raise ValueError(f"Required field {field_name} missing in namespace {namespace}")
        
        # Validate all provided fields
        for field_name, value in fields_dict.items():
            if field_name not in namespace_fields:
                raise ValueError(f"Invalid extension field: {field_name} in namespace {namespace}")
            
            if not validate_extension_value(namespace_fields[field_name], value):
                raise ValueError(f"Invalid value for extension field: {field_name} in namespace {namespace}") 