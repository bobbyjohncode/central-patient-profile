from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import hmac
import hashlib
import os
from datetime import datetime

from app.services.hint_sync import HintSyncService
from app.core.config import settings
from app.db.test_db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
    responses={
        400: {"description": "Invalid webhook payload"},
        401: {"description": "Invalid webhook signature"},
        500: {"description": "Internal server error"}
    }
)

class HintWebhookEvent(BaseModel):
    """Schema for Hint webhook events."""
    event_type: str = Field(..., description="Type of event (e.g., patient.created, patient.updated)")
    patient_id: str = Field(..., description="Hint's patient ID")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")

async def verify_webhook_signature(request: Request) -> bool:
    """Verify the webhook signature from Hint.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if signature is valid
        
    Raises:
        HTTPException: If signature is invalid
    """
    signature = request.headers.get("X-Hint-Signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
        
    # Get webhook secret from environment
    webhook_secret = os.getenv("HINT_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
        
    # Get raw body
    body = await request.body()
    
    # Calculate expected signature
    expected = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
    return True

async def process_patient_sync(patient_id: str, event_type: str, db: AsyncSession):
    """Process patient sync in background.
    
    Args:
        patient_id: Hint's patient ID
        event_type: Type of event
        db: Database session
    """
    try:
        sync_service = HintSyncService()
        
        # Fetch and map patient data
        profile = await sync_service.sync_patient_by_id(patient_id)
        
        # TODO: Save profile to database
        # For now, we'll just log it
        print(f"Synced patient {patient_id} from event {event_type}")
        
    except Exception as e:
        # Log error but don't raise to prevent webhook retries
        print(f"Error processing webhook for patient {patient_id}: {str(e)}")

@router.post("/hint", status_code=202)
async def handle_hint_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Handle incoming webhooks from Hint.
    
    This endpoint:
    1. Verifies the webhook signature
    2. Parses the event type and patient ID
    3. Queues a background task to sync the patient
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        JSON response with status
        
    Raises:
        HTTPException: If webhook is invalid
    """
    # Verify webhook signature
    await verify_webhook_signature(request)
    
    # Parse webhook payload
    try:
        payload = await request.json()
        event = HintWebhookEvent(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid webhook payload: {str(e)}")
        
    # Validate event type
    if not event.event_type.startswith("patient."):
        raise HTTPException(status_code=400, detail="Invalid event type")
        
    # Queue background task
    background_tasks.add_task(
        process_patient_sync,
        event.patient_id,
        event.event_type,
        db
    )
    
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "message": f"Processing {event.event_type} for patient {event.patient_id}"
        }
    ) 