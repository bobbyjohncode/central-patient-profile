from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientResponse, PatientSyncRequest, PatientSyncResponse

router = APIRouter()

@router.post("/", response_model=PatientResponse)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    try:
        db_patient = Patient(**patient.model_dump())
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return db_patient
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="A patient with this email already exists"
        )

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.get("/", response_model=List[PatientResponse])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@router.post("/sync", response_model=PatientSyncResponse)
def sync_patients(sync_request: PatientSyncRequest, db: Session = Depends(get_db)):
    # Get all existing patients
    existing_patients = {p.email: p for p in db.query(Patient).all()}
    sync_emails = {p.email for p in sync_request.patients}
    
    # Check for duplicate emails in the sync request
    if len(sync_emails) != len(sync_request.patients):
        raise HTTPException(
            status_code=400,
            detail="Duplicate emails found in sync request"
        )
    
    created = 0
    updated = 0
    deleted = 0
    
    # Process each patient in the sync request
    for patient_data in sync_request.patients:
        if patient_data.email in existing_patients:
            # Update existing patient
            existing_patient = existing_patients[patient_data.email]
            for key, value in patient_data.model_dump().items():
                setattr(existing_patient, key, value)
            updated += 1
        else:
            # Create new patient
            new_patient = Patient(**patient_data.model_dump())
            db.add(new_patient)
            created += 1
    
    # Delete patients not in sync request
    for email, patient in existing_patients.items():
        if email not in sync_emails:
            db.delete(patient)
            deleted += 1
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="A patient with one of the provided emails already exists"
        )
    
    return PatientSyncResponse(
        synced=len(sync_request.patients),
        created=created,
        updated=updated,
        deleted=deleted
    )
