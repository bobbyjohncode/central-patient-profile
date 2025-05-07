import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field, validator
from datetime import date
import re

class ValidationRule(BaseModel):
    """Validation rules for extension fields.
    
    Attributes:
        pattern: Optional regex pattern for string validation
        min_length: Optional minimum length for string/number
        max_length: Optional maximum length for string/number
        enum: Optional list of allowed values
    """
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    enum: Optional[List[str]] = None

class ExtensionField(BaseModel):
    """Definition of an extension field.
    
    Attributes:
        name: Field name in the external system
        type: Data type (string, number, boolean, date)
        namespace: Vendor/system namespace
        description: Field description
        required: Whether the field is required
        validation: Optional validation rules
    """
    name: str
    type: str
    namespace: str
    description: str
    required: bool = False
    validation: Optional[ValidationRule] = None

    @validator('type')
    def validate_type(cls, v: str) -> str:
        """Validate that the field type is supported.
        
        Args:
            v: Type to validate
            
        Returns:
            Validated type
            
        Raises:
            ValueError: If type is not supported
        """
        valid_types = {'string', 'number', 'boolean', 'date'}
        if v not in valid_types:
            raise ValueError(f'Type must be one of {valid_types}')
        return v

class ExtensionFields(BaseModel):
    """Collection of extension field definitions.
    
    Attributes:
        fields: List of extension field definitions
    """
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

class ExtensionManager:
    """Manages extension fields and their validation.
    
    This class handles loading and validating extension field definitions
    from YAML files, and provides methods to validate extension data
    against these definitions.
    
    The extension system allows for dynamic field definitions without
    code changes, making it easy to add support for new vendor systems
    or field types.
    """
    
    def __init__(self, yaml_path: str = "app/schemas/extension_fields.yaml"):
        """Initialize the extension manager.
        
        Args:
            yaml_path: Path to the extension fields YAML file
        """
        self.schema_file = Path(yaml_path)
        self.extension_schemas = self._load_schemas()
        self._validate_schemas()

    def _load_schemas(self) -> Dict[str, Any]:
        """Load extension schemas from YAML file.
        
        Returns:
            Dict containing extension field definitions
            
        Raises:
            FileNotFoundError: If YAML file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        if not self.schema_file.exists():
            raise FileNotFoundError(f"Extension fields YAML file not found: {self.schema_file}")
            
        with open(self.schema_file, "r") as f:
            return yaml.safe_load(f)

    def _validate_schemas(self) -> None:
        """Validate loaded schemas for consistency.
        
        Raises:
            ValueError: If schemas are invalid
        """
        if not isinstance(self.extension_schemas, dict):
            raise ValueError("Extension schemas must be a dictionary")
            
        for namespace, schema in self.extension_schemas.items():
            if not isinstance(schema, dict):
                raise ValueError(f"Schema for {namespace} must be a dictionary")
                
            if "required" in schema and not isinstance(schema["required"], list):
                raise ValueError(f"Required fields for {namespace} must be a list")
                
            if "fields" in schema and not isinstance(schema["fields"], dict):
                raise ValueError(f"Fields for {namespace} must be a dictionary")

    def validate_extensions(self, extensions: Dict[str, Any]) -> None:
        """Validate extension fields against their schemas.
        
        Args:
            extensions: Extension data to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not extensions:
            return

        for namespace, data in extensions.items():
            if namespace not in self.extension_schemas:
                raise ValueError(f"Unknown extension namespace: {namespace}")

            schema = self.extension_schemas[namespace]
            
            # Check required fields
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field '{field}' in {namespace} extension")

            # Validate field types
            field_types = schema.get("fields", {})
            for field, value in data.items():
                if field in field_types:
                    expected_type = field_types[field]["type"]
                    if not self._validate_field_type(value, expected_type):
                        raise ValueError(
                            f"Field '{field}' in {namespace} extension must be of type {expected_type}"
                        )

    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validate a value against its expected type.
        
        Args:
            value: Value to validate
            expected_type: Expected type name
            
        Returns:
            True if value matches type, False otherwise
        """
        if expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "date":
            if isinstance(value, str):
                try:
                    date.fromisoformat(value)
                    return True
                except ValueError:
                    return False
            return isinstance(value, date)
        return False

    def get_namespace_fields(self, namespace: str) -> Dict[str, Any]:
        """Get field definitions for a namespace.
        
        Args:
            namespace: Namespace to get fields for
            
        Returns:
            Dict of field definitions
            
        Raises:
            ValueError: If namespace doesn't exist
        """
        if namespace not in self.extension_schemas:
            raise ValueError(f"Unknown namespace: {namespace}")
        return self.extension_schemas[namespace].get("fields", {})

    def get_required_fields(self, namespace: str) -> List[str]:
        """Get required fields for a namespace.
        
        Args:
            namespace: Namespace to get required fields for
            
        Returns:
            List of required field names
            
        Raises:
            ValueError: If namespace doesn't exist
        """
        if namespace not in self.extension_schemas:
            raise ValueError(f"Unknown namespace: {namespace}")
        return self.extension_schemas[namespace].get("required", []) 