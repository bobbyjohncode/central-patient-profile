from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime

from app.services.hint_sync import HintSyncService
from app.core.config import settings
from app.db.test_db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/sync/hint",
    tags=["hint"],
    responses={
        404: {"description": "Patient not found"},
        401: {"description": "Invalid API key"},
        500: {"description": "Internal server error"}
    }
)

class SyncResponse(BaseModel):
    """Response model for manual sync endpoint."""
    patient_id: str
    profile: Dict[str, Any]
    synced_at: datetime
    status: str = "success"

@router.get("/{patient_id}", response_model=SyncResponse)
async def sync_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
) -> SyncResponse:
    """Manually trigger sync for a Hint patient.
    
    This endpoint:
    1. Fetches the patient from Hint's API
    2. Maps the data to internal profile format
    3. Returns the mapped profile for debugging
    
    Args:
        patient_id: Hint's patient ID
        db: Database session
        
    Returns:
        SyncResponse containing the mapped profile
        
    Raises:
        HTTPException: If patient not found or sync fails
    """
    try:
        sync_service = HintSyncService()
        
        # Fetch and map patient data
        profile = await sync_service.sync_patient_by_id(patient_id)
        
        return SyncResponse(
            patient_id=patient_id,
            profile=profile,
            synced_at=datetime.utcnow(),
            status="success"
        )
        
    except HTTPException as e:
        # Re-raise HTTP exceptions (e.g., 404, 401)
        raise e
    except Exception as e:
        # Log error and raise 500
        print(f"Error syncing patient {patient_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync patient: {str(e)}"
        ) 