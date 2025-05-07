import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
from pydantic import BaseModel, Field
from functools import lru_cache

class ExtensionField(BaseModel):
    """Schema for extension field definitions."""
    name: str = Field(..., description="Field name")
    type: str = Field(..., description="Field type (string, number, boolean, date, array, object)")
    description: str = Field(..., description="Field description")
    required: bool = Field(default=False, description="Whether field is required")
    default: Any = Field(default=None, description="Default value")
    validation: Optional[Dict[str, Any]] = Field(default=None, description="Validation rules")
    enum: Optional[List[Any]] = Field(default=None, description="Allowed values for enum types")

class ExtensionNamespace(BaseModel):
    """Schema for extension namespace definitions."""
    name: str = Field(..., description="Namespace name (e.g., hint, epic)")
    description: str = Field(..., description="Namespace description")
    fields: Dict[str, ExtensionField] = Field(..., description="Field definitions")
    required_fields: List[str] = Field(default_factory=list, description="Required field names")

def load_extension_fields_from_yaml() -> Dict[str, ExtensionNamespace]:
    """Load extension field definitions from YAML files.
    
    This function:
    1. Reads YAML files from the extensions/ directory
    2. Validates field definitions against schemas
    3. Organizes fields by namespace
    4. Tracks required fields
    
    Returns:
        Dict mapping namespace names to ExtensionNamespace objects
        
    Raises:
        ValueError: If YAML files are invalid or missing required fields
    """
    extensions_dir = Path(__file__).parent.parent / "extensions"
    if not extensions_dir.exists():
        raise ValueError(f"Extensions directory not found: {extensions_dir}")
        
    namespaces = {}
    
    # Load each YAML file in the extensions directory
    for yaml_file in extensions_dir.glob("*.yaml"):
        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)
                
            if not isinstance(data, dict):
                raise ValueError(f"Invalid YAML format in {yaml_file}")
                
            # Extract namespace info
            namespace_name = data.get("namespace")
            if not namespace_name:
                raise ValueError(f"Missing namespace in {yaml_file}")
                
            # Parse fields
            fields = {}
            required_fields = []
            
            for field_name, field_data in data.get("fields", {}).items():
                # Create field definition
                field = ExtensionField(
                    name=field_name,
                    **field_data
                )
                fields[field_name] = field
                
                # Track required fields
                if field.required:
                    required_fields.append(field_name)
                    
            # Create namespace
            namespace = ExtensionNamespace(
                name=namespace_name,
                description=data.get("description", ""),
                fields=fields,
                required_fields=required_fields
            )
            
            namespaces[namespace_name] = namespace
            
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing {yaml_file}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing {yaml_file}: {str(e)}")
            
    if not namespaces:
        raise ValueError("No valid extension definitions found")
        
    return namespaces

# Load extension fields at module import
try:
    EXTENSION_FIELDS = load_extension_fields_from_yaml()
except Exception as e:
    print(f"Warning: Failed to load extension fields: {str(e)}")
    EXTENSION_FIELDS = {}

@lru_cache()
def get_settings() -> "Settings":
    """Get application settings from environment variables."""
    return Settings()

class Settings(BaseModel):
    """Application settings."""
    # Database settings
    DATABASE_URL: str = Field(..., description="Database connection URL")
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Central Patient Profile"
    
    # Security settings
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Extension settings
    EXTENSION_FIELDS: Dict[str, ExtensionNamespace] = EXTENSION_FIELDS
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = get_settings() 