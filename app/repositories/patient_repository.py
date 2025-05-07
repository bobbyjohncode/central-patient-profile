from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate, PatientSyncRequest
from app.core.extensions import ExtensionManager
from app.services.trust_score import TrustScoreCalculator

class PatientRepository:
    """Repository for managing patient records in the database.
    
    This repository implements the repository pattern to abstract database operations
    and provide a clean interface for patient data management. It handles:
    - CRUD operations for patient records
    - Field ownership tracking
    - Extension validation
    - Trust score calculation
    - Multi-system synchronization
    
    The repository ensures that core identity fields are protected and that
    all operations maintain data integrity and proper field ownership.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize the repository with a database session.
        
        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.extension_manager = ExtensionManager()
        self.trust_calculator = TrustScoreCalculator()

    async def create(self, patient_data: PatientCreate, source_system: str = "manual") -> Patient:
        """Create a new patient record with field ownership tracking.
        
        Args:
            patient_data: Patient data to create
            source_system: System creating the record (default: "manual")
            
        Returns:
            Created patient record
            
        Raises:
            ValueError: If required fields are missing
            ValidationError: If extension fields are invalid
        """
        # Validate core fields
        if not all(getattr(patient_data, field) for field in ['first_name', 'last_name', 'email', 'date_of_birth']):
            raise ValueError("Missing required core fields")
            
        db_patient = Patient(**patient_data.model_dump(exclude={'extensions'}))
        
        # Set field ownership for all provided fields
        field_ownership = {}
        for field in patient_data.model_fields:
            if getattr(patient_data, field) is not None:
                field_ownership[field] = source_system
        db_patient.field_ownership = field_ownership
        
        if patient_data.extensions:
            self.extension_manager.validate_extensions(patient_data.extensions)
            db_patient.extensions = patient_data.extensions
            
        db_patient.last_sync_at = datetime.now()
        db_patient.trust_score = self.trust_calculator.calculate_score(db_patient)
        
        self.db.add(db_patient)
        await self.db.flush()
        await self.db.refresh(db_patient)
        return db_patient

    async def get(self, patient_id: int) -> Optional[Patient]:
        """Get a patient by ID.
        
        Args:
            patient_id: ID of the patient to retrieve
            
        Returns:
            Patient record if found, None otherwise
        """
        return await self.db.get(Patient, patient_id)

    async def get_by_email(self, email: str) -> Optional[Patient]:
        """Get a patient by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Patient record if found, None otherwise
        """
        stmt = select(Patient).where(Patient.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """List patients with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of patient records
        """
        stmt = select(Patient).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, patient_id: int, patient_data: PatientUpdate, 
                    source_system: str = "manual") -> Optional[Patient]:
        """Update a patient record with field ownership tracking.
        
        Args:
            patient_id: ID of the patient to update
            patient_data: New patient data
            source_system: System performing the update (default: "manual")
            
        Returns:
            Updated patient record if found, None otherwise
            
        Raises:
            ValidationError: If extension fields are invalid
        """
        db_patient = await self.get(patient_id)
        if not db_patient:
            return None

        update_data = patient_data.model_dump(exclude_unset=True, exclude={'extensions'})
        
        # Update field ownership for changed fields
        if not db_patient.field_ownership:
            db_patient.field_ownership = {}
            
        for field, value in update_data.items():
            if value is not None:
                setattr(db_patient, field, value)
                db_patient.field_ownership[field] = source_system

        if patient_data.extensions is not None:
            self.extension_manager.validate_extensions(patient_data.extensions)
            db_patient.extensions = patient_data.extensions

        db_patient.last_sync_at = datetime.now()
        db_patient.trust_score = self.trust_calculator.calculate_score(db_patient)
        
        await self.db.flush()
        await self.db.refresh(db_patient)
        return db_patient

    async def delete(self, patient_id: int) -> bool:
        """Delete a patient record.
        
        Args:
            patient_id: ID of the patient to delete
            
        Returns:
            True if deleted, False if not found
        """
        stmt = delete(Patient).where(Patient.id == patient_id)
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def sync_patients(self, sync_data: PatientSyncRequest, 
                          source_system: str) -> Dict[str, Any]:
        """Sync patients from an external system.
        
        This method handles batch synchronization of patient records from an
        external system, including creation, updates, and optional deletion
        of missing records.
        
        Args:
            sync_data: Sync request containing patient data
            source_system: System performing the sync
            
        Returns:
            Dict containing operation counts and any errors
            
        Raises:
            ValidationError: If any patient data is invalid
        """
        created = 0
        updated = 0
        deleted = 0
        errors = []

        for patient_data in sync_data.patients:
            try:
                existing_patient = await self.get_by_email(patient_data.email)
                if existing_patient:
                    update_data = PatientUpdate(**patient_data.model_dump())
                    await self.update(existing_patient.id, update_data, source_system)
                    updated += 1
                else:
                    create_data = PatientCreate(**patient_data.model_dump())
                    await self.create(create_data, source_system)
                    created += 1
            except Exception as e:
                errors.append(f"Error processing patient {patient_data.email}: {str(e)}")

        if sync_data.delete_missing:
            existing_emails = {p.email for p in await self.list()}
            sync_emails = {p.email for p in sync_data.patients}
            emails_to_delete = existing_emails - sync_emails

            for email in emails_to_delete:
                try:
                    patient = await self.get_by_email(email)
                    if patient:
                        await self.delete(patient.id)
                        deleted += 1
                except Exception as e:
                    errors.append(f"Error deleting patient {email}: {str(e)}")

        return {
            "created": created,
            "updated": updated,
            "deleted": deleted,
            "errors": errors
        } 