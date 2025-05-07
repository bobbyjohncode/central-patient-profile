from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.test_db import get_db
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import (
    Patient, PatientCreate, PatientUpdate, 
    PatientSyncRequest, PatientSyncResponse
)

router = APIRouter(
    prefix="/patients",
    tags=["patients"],
    responses={
        404: {"description": "Patient not found"},
        500: {"description": "Internal server error"}
    }
)

@router.post(
    "/",
    response_model=Patient,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Patient created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "date_of_birth": "1990-01-01",
                        "gender": "male",
                        "extensions": {
                            "hint": {
                                "membership_status": "active"
                            }
                        },
                        "field_ownership": {
                            "first_name": "manual",
                            "last_name": "manual",
                            "email": "manual"
                        },
                        "trust_score": 85,
                        "created_at": "2024-03-20T10:00:00Z",
                        "updated_at": None,
                        "last_sync_at": "2024-03-20T10:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Missing required core fields"
                    }
                }
            }
        }
    }
)
async def create_patient(
    patient: PatientCreate,
    source_system: str = Query(
        "manual",
        description="System creating the patient record",
        example="hint",
        pattern="^[a-z_]+$"
    ),
    db: AsyncSession = Depends(get_db)
) -> Patient:
    """Create a new patient record.
    
    This endpoint creates a new patient record with field ownership tracking
    and extension validation. Core identity fields are required and validated.
    
    The endpoint supports dynamic extension fields defined in YAML configuration,
    allowing for flexible integration with external systems without code changes.
    
    Args:
        patient: Patient data to create
        source_system: System creating the record (default: "manual")
        db: Database session
        
    Returns:
        Created patient record
        
    Raises:
        HTTPException: If validation fails or database error occurs
    """
    try:
        repo = PatientRepository(db)
        return await repo.create(patient, source_system)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/{patient_id}",
    response_model=Patient,
    responses={
        200: {
            "description": "Patient found successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "date_of_birth": "1990-01-01",
                        "gender": "male",
                        "extensions": {
                            "hint": {
                                "membership_status": "active"
                            }
                        },
                        "field_ownership": {
                            "first_name": "hint",
                            "last_name": "hint",
                            "email": "hint"
                        },
                        "trust_score": 85,
                        "created_at": "2024-03-20T10:00:00Z",
                        "updated_at": "2024-03-20T11:00:00Z",
                        "last_sync_at": "2024-03-20T11:00:00Z"
                    }
                }
            }
        }
    }
)
async def get_patient(
    patient_id: int = Path(
        ...,
        description="ID of the patient to retrieve",
        example=1,
        ge=1
    ),
    db: AsyncSession = Depends(get_db)
) -> Patient:
    """Get a patient by ID.
    
    This endpoint retrieves a patient record by its unique identifier.
    The response includes all patient fields, including extensions and
    field ownership information.
    
    Args:
        patient_id: ID of the patient to retrieve
        db: Database session
        
    Returns:
        Patient record if found
        
    Raises:
        HTTPException: If patient not found
    """
    repo = PatientRepository(db)
    patient = await repo.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.get(
    "/email/{email}",
    response_model=Patient,
    responses={
        200: {
            "description": "Patient found successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "date_of_birth": "1990-01-01",
                        "gender": "male",
                        "extensions": {
                            "hint": {
                                "membership_status": "active"
                            }
                        },
                        "field_ownership": {
                            "first_name": "hint",
                            "last_name": "hint",
                            "email": "hint"
                        },
                        "trust_score": 85,
                        "created_at": "2024-03-20T10:00:00Z",
                        "updated_at": "2024-03-20T11:00:00Z",
                        "last_sync_at": "2024-03-20T11:00:00Z"
                    }
                }
            }
        }
    }
)
async def get_patient_by_email(
    email: str = Path(
        ...,
        description="Email address to search for",
        example="john.doe@example.com",
        pattern="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    ),
    db: AsyncSession = Depends(get_db)
) -> Patient:
    """Get a patient by email address.
    
    This endpoint retrieves a patient record by their email address.
    Email addresses are unique in the system, so this will return at most
    one patient record.
    
    Args:
        email: Email address to search for
        db: Database session
        
    Returns:
        Patient record if found
        
    Raises:
        HTTPException: If patient not found
    """
    repo = PatientRepository(db)
    patient = await repo.get_by_email(email)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.get(
    "/",
    response_model=List[Patient],
    responses={
        200: {
            "description": "List of patients retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "john.doe@example.com",
                            "date_of_birth": "1990-01-01",
                            "gender": "male",
                            "extensions": {
                                "hint": {
                                    "membership_status": "active"
                                }
                            },
                            "field_ownership": {
                                "first_name": "hint",
                                "last_name": "hint",
                                "email": "hint"
                            },
                            "trust_score": 85,
                            "created_at": "2024-03-20T10:00:00Z",
                            "updated_at": "2024-03-20T11:00:00Z",
                            "last_sync_at": "2024-03-20T11:00:00Z"
                        }
                    ]
                }
            }
        }
    }
)
async def list_patients(
    skip: int = Query(
        0,
        description="Number of records to skip",
        ge=0,
        example=0
    ),
    limit: int = Query(
        100,
        description="Maximum number of records to return",
        ge=1,
        le=1000,
        example=10
    ),
    db: AsyncSession = Depends(get_db)
) -> List[Patient]:
    """List patients with pagination.
    
    This endpoint retrieves a paginated list of patient records. The response
    includes all patient fields, including extensions and field ownership
    information.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of patient records
    """
    repo = PatientRepository(db)
    return await repo.list(skip, limit)

@router.patch(
    "/{patient_id}",
    response_model=Patient,
    responses={
        200: {
            "description": "Patient updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "date_of_birth": "1990-01-01",
                        "gender": "male",
                        "extensions": {
                            "hint": {
                                "membership_status": "active"
                            }
                        },
                        "field_ownership": {
                            "first_name": "hint",
                            "last_name": "hint",
                            "email": "hint"
                        },
                        "trust_score": 85,
                        "created_at": "2024-03-20T10:00:00Z",
                        "updated_at": "2024-03-20T11:00:00Z",
                        "last_sync_at": "2024-03-20T11:00:00Z"
                    }
                }
            }
        }
    }
)
async def update_patient(
    patient_id: int = Path(
        ...,
        description="ID of the patient to update",
        example=1,
        ge=1
    ),
    patient: PatientUpdate = None,
    source_system: str = Query(
        "manual",
        description="System performing the update",
        example="hint",
        pattern="^[a-z_]+$"
    ),
    db: AsyncSession = Depends(get_db)
) -> Patient:
    """Update a patient record.
    
    This endpoint updates a patient record with field ownership tracking
    and extension validation. Only provided fields are updated.
    
    The endpoint maintains field ownership information, updating it for
    any fields that are modified. Extension fields are validated against
    their YAML definitions.
    
    Args:
        patient_id: ID of the patient to update
        patient: New patient data
        source_system: System performing the update (default: "manual")
        db: Database session
        
    Returns:
        Updated patient record
        
    Raises:
        HTTPException: If patient not found or validation fails
    """
    repo = PatientRepository(db)
    updated_patient = await repo.update(patient_id, patient, source_system)
    if not updated_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return updated_patient

@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Patient deleted successfully"}
    }
)
async def delete_patient(
    patient_id: int = Path(
        ...,
        description="ID of the patient to delete",
        example=1,
        ge=1
    ),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a patient record.
    
    This endpoint permanently deletes a patient record from the system.
    The operation cannot be undone.
    
    Args:
        patient_id: ID of the patient to delete
        db: Database session
        
    Raises:
        HTTPException: If patient not found
    """
    repo = PatientRepository(db)
    success = await repo.delete(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")

@router.post(
    "/sync",
    response_model=PatientSyncResponse,
    responses={
        200: {
            "description": "Sync completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "created": 2,
                        "updated": 1,
                        "deleted": 0,
                        "errors": []
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid extension field: membership_status in namespace hint"
                    }
                }
            }
        }
    }
)
async def sync_patients(
    sync_data: PatientSyncRequest,
    db: AsyncSession = Depends(get_db)
) -> PatientSyncResponse:
    """Sync patients from an external system.
    
    This endpoint handles batch synchronization of patient records from an
    external system, including creation, updates, and optional deletion
    of missing records.
    
    The sync operation:
    - Creates new patients that don't exist
    - Updates existing patients with new data
    - Optionally deletes patients that no longer exist in the source
    - Maintains field ownership information
    - Validates all extension fields
    
    Args:
        sync_data: Sync request containing patient data
        db: Database session
        
    Returns:
        Sync operation results
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        repo = PatientRepository(db)
        result = await repo.sync_patients(sync_data, sync_data.source_system)
        return PatientSyncResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/{patient_id}/trust-score",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Trust score retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "overall_score": 85,
                        "breakdown": {
                            "field_completeness": (100, 0.3),
                            "data_freshness": (80, 0.2),
                            "extension_completeness": (90, 0.3),
                            "field_ownership": (70, 0.2)
                        }
                    }
                }
            }
        }
    }
)
async def get_trust_score(
    patient_id: int = Path(
        ...,
        description="ID of the patient to check",
        example=1,
        ge=1
    ),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed trust score breakdown for a patient.
    
    This endpoint provides a detailed breakdown of the patient's trust score,
    including individual component scores and weights.
    
    The trust score is calculated based on:
    - Field completeness (30%)
    - Data freshness (20%)
    - Extension completeness (30%)
    - Field ownership (20%)
    
    Args:
        patient_id: ID of the patient to check
        db: Database session
        
    Returns:
        Dict containing trust score breakdown
        
    Raises:
        HTTPException: If patient not found
    """
    repo = PatientRepository(db)
    patient = await repo.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    return {
        "overall_score": patient.trust_score,
        "breakdown": repo.trust_calculator.get_score_breakdown(patient)
    }
