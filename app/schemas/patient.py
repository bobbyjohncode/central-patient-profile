from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    email: EmailStr
    phone: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PatientSyncRequest(BaseModel):
    patients: List[PatientCreate]

class PatientSyncResponse(BaseModel):
    synced: int
    created: int
    updated: int
    deleted: int