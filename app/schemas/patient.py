from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    email: EmailStr
    phone: Optional[str] = None
    extensions: Dict[str, Any] = Field(default_factory=dict)

class PatientCreate(PatientBase):
    pass

class PatientUpdate(PatientBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None

class PatientInDBBase(PatientBase):
    id: int

    class Config:
        from_attributes = True

class Patient(PatientInDBBase):
    pass

class PatientInDB(PatientInDBBase):
    pass

class PatientResponse(PatientInDBBase):
    model_config = ConfigDict(from_attributes=True)

class PatientSyncRequest(BaseModel):
    patients: List[PatientCreate]

class PatientSyncResponse(BaseModel):
    synced: int
    created: int
    updated: int
    deleted: int