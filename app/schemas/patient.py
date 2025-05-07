from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    email: EmailStr
    gender: Optional[str] = None
    extensions: Dict[str, Any] = Field(default_factory=dict)

class PatientCreate(PatientBase):
    pass

class PatientUpdate(PatientBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    extensions: Optional[Dict[str, Any]] = None

class PatientInDBBase(PatientBase):
    id: int
    field_ownership: Dict[str, str] = Field(default_factory=dict)
    trust_score: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Patient(PatientInDBBase):
    pass

class PatientInDB(PatientInDBBase):
    pass

class PatientResponse(PatientInDBBase):
    pass

class PatientSyncRequest(BaseModel):
    patients: List[PatientCreate]
    delete_missing: bool = False
    source_system: str  # System performing the sync (e.g., "hint", "elation")

class PatientSyncResponse(BaseModel):
    created: int
    updated: int
    deleted: int
    errors: List[str]