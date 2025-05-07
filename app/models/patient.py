from sqlalchemy import Column, Integer, String, Date, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.sql import func
from typing import Dict, Any, Optional
from app.db.base_class import Base

class Patient(Base):
    """Core patient profile model that serves as the central source of truth.
    
    This model maintains the canonical patient record while tracking field ownership
    and data quality metrics. Core identity fields (first_name, last_name, email, dob)
    are protected and should only be modified through validated update operations.
    
    Extensions are stored in a namespaced JSON structure, allowing each vendor system
    to maintain its own data without schema changes. Field definitions are loaded
    dynamically from YAML configuration files.
    
    Attributes:
        id: Unique identifier for the patient record
        first_name: Patient's first name (core identity field)
        last_name: Patient's last name (core identity field)
        email: Unique email address (core identity field)
        date_of_birth: Patient's date of birth (core identity field)
        gender: Patient's gender
        extensions: Namespaced JSON object for vendor-specific fields
        field_ownership: Maps field names to their source system
        trust_score: Data quality score (0-100)
        created_at: Timestamp of record creation
        updated_at: Timestamp of last update
        last_sync_at: Timestamp of last successful sync
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String)
    extensions = Column(MutableDict.as_mutable(JSON), default=dict)
    field_ownership = Column(MutableDict.as_mutable(JSON), default=dict)
    trust_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync_at = Column(DateTime(timezone=True))

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary.
        
        Returns:
            Dict containing all patient fields, with dates converted to ISO format
            and empty extensions defaulting to empty dict.
        """
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "email": self.email,
            "gender": self.gender,
            "extensions": self.extensions or {},
            "field_ownership": self.field_ownership or {},
            "trust_score": self.trust_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None
        }

    def get_extension(self, namespace: str) -> Dict[str, Any]:
        """Get extension fields for a specific namespace.
        
        Args:
            namespace: The vendor/system namespace to retrieve
            
        Returns:
            Dict of extension fields for the specified namespace
        """
        return self.extensions.get(namespace, {})

    def set_extension(self, namespace: str, fields: Dict[str, Any]) -> None:
        """Set extension fields for a specific namespace.
        
        Args:
            namespace: The vendor/system namespace to update
            fields: Dict of extension fields to set
        """
        if not self.extensions:
            self.extensions = {}
        self.extensions[namespace] = fields

    def get_field_owner(self, field: str) -> Optional[str]:
        """Get the system that owns a specific field.
        
        Args:
            field: The field name to check
            
        Returns:
            Name of the system that owns the field, or None if not owned
        """
        return self.field_ownership.get(field)

    def set_field_owner(self, field: str, system: str) -> None:
        """Set the system that owns a specific field.
        
        Args:
            field: The field name to update
            system: The system name to set as owner
        """
        if not self.field_ownership:
            self.field_ownership = {}
        self.field_ownership[field] = system