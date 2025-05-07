from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientSyncRequest,
    PatientSyncResponse
)
from app.core.extensions import validate_extensions

router = APIRouter()

@router.post("/", response_model=PatientResponse)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient with optional extension fields."""
    try:
        validate_extensions(patient.extensions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    db_patient = Patient(**patient.dict())
    try:
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return db_patient.to_dict()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="A patient with this email already exists"
        )

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """Get a patient by ID."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient.to_dict()

@router.get("/", response_model=List[PatientResponse])
def list_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all patients."""
    patients = db.query(Patient).offset(skip).limit(limit).all()
    return [patient.to_dict() for patient in patients]

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db)
):
    """Update a patient's information and extensions."""
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Validate extensions if provided
    if patient_update.extensions:
        try:
            validate_extensions(patient_update.extensions)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Update patient fields
    update_data = patient_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_patient, field, value)
    
    try:
        db.commit()
        db.refresh(db_patient)
        return db_patient.to_dict()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="A patient with this email already exists"
        )

@router.post("/sync", response_model=PatientSyncResponse)
def sync_patients(sync_request: PatientSyncRequest, db: Session = Depends(get_db)):
    """Sync multiple patients, handling extensions."""
    synced = 0
    created = 0
    updated = 0
    deleted = 0
    
    try:
        # Get all existing patients
        existing_patients = {p.email: p for p in db.query(Patient).all()}
        new_emails = {p.email for p in sync_request.patients}
        
        print(f"Existing patients: {list(existing_patients.keys())}")
        print(f"New emails: {list(new_emails)}")
        
        # Delete patients not in the new list
        for email, patient in existing_patients.items():
            if email not in new_emails:
                print(f"Deleting patient with email: {email}")
                db.delete(patient)
                deleted += 1
        
        # Create or update patients
        for patient_data in sync_request.patients:
            try:
                validate_extensions(patient_data.extensions)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            
            if patient_data.email in existing_patients:
                # Update existing patient
                print(f"Updating patient with email: {patient_data.email}")
                patient = existing_patients[patient_data.email]
                update_data = patient_data.dict()
                for field, value in update_data.items():
                    setattr(patient, field, value)
                updated += 1
            else:
                # Create new patient
                print(f"Creating new patient with email: {patient_data.email}")
                db_patient = Patient(**patient_data.dict())
                db.add(db_patient)
                created += 1
            synced += 1
        
        # Commit all changes in a single transaction
        db.commit()
        
        print(f"Final stats: synced={synced}, created={created}, updated={updated}, deleted={deleted}")
        
        return PatientSyncResponse(
            synced=synced,
            created=created,
            updated=updated,
            deleted=deleted
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="A patient with one of the provided emails already exists"
        )
