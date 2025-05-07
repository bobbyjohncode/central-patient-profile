from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.test_db import get_db
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientSyncRequest,
    PatientSyncResponse
)
from app.repositories.patient_repository import PatientRepository

router = APIRouter()

@router.post("/", response_model=PatientResponse)
async def create_patient(
    patient: PatientCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new patient."""
    repository = PatientRepository(db)
    db_patient = await repository.create(patient)
    return db_patient

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a patient by ID."""
    repository = PatientRepository(db)
    db_patient = await repository.get(patient_id)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all patients."""
    repository = PatientRepository(db)
    patients = await repository.list(skip=skip, limit=limit)
    return patients

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient: PatientUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a patient."""
    repository = PatientRepository(db)
    db_patient = await repository.update(patient_id, patient)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a patient."""
    repository = PatientRepository(db)
    success = await repository.delete(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient deleted successfully"}

@router.post("/sync", response_model=PatientSyncResponse)
async def sync_patients(
    sync_data: PatientSyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """Sync patients from external system."""
    repository = PatientRepository(db)
    result = await repository.sync_patients(sync_data)
    return PatientSyncResponse(**result)
