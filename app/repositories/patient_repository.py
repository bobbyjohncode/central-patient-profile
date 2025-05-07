from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate, PatientSyncRequest
from app.core.extensions import ExtensionManager

class PatientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.extension_manager = ExtensionManager()

    async def create(self, patient_data: PatientCreate) -> Patient:
        """Create a new patient."""
        db_patient = Patient(**patient_data.model_dump(exclude={'extensions'}))
        if patient_data.extensions:
            self.extension_manager.validate_extensions(patient_data.extensions)
            db_patient.extensions = patient_data.extensions
        self.db.add(db_patient)
        await self.db.flush()
        await self.db.refresh(db_patient)
        return db_patient

    async def get(self, patient_id: int) -> Optional[Patient]:
        """Get a patient by ID."""
        return await self.db.get(Patient, patient_id)

    async def get_by_email(self, email: str) -> Optional[Patient]:
        """Get a patient by email."""
        stmt = select(Patient).where(Patient.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """List all patients with pagination."""
        stmt = select(Patient).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, patient_id: int, patient_data: PatientUpdate) -> Optional[Patient]:
        """Update a patient."""
        db_patient = await self.get(patient_id)
        if not db_patient:
            return None

        update_data = patient_data.model_dump(exclude_unset=True, exclude={'extensions'})
        for field, value in update_data.items():
            setattr(db_patient, field, value)

        if patient_data.extensions is not None:
            self.extension_manager.validate_extensions(patient_data.extensions)
            db_patient.extensions = patient_data.extensions

        await self.db.flush()
        await self.db.refresh(db_patient)
        return db_patient

    async def delete(self, patient_id: int) -> bool:
        """Delete a patient."""
        stmt = delete(Patient).where(Patient.id == patient_id)
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def sync_patients(self, sync_data: PatientSyncRequest) -> Dict[str, Any]:
        """Sync patients from external system."""
        created = 0
        updated = 0
        deleted = 0
        errors = []

        # Process patients to create or update
        for patient_data in sync_data.patients:
            try:
                existing_patient = await self.get_by_email(patient_data.email)
                if existing_patient:
                    # Update existing patient
                    update_data = PatientUpdate(**patient_data.model_dump())
                    await self.update(existing_patient.id, update_data)
                    updated += 1
                else:
                    # Create new patient
                    create_data = PatientCreate(**patient_data.model_dump())
                    await self.create(create_data)
                    created += 1
            except Exception as e:
                errors.append(f"Error processing patient {patient_data.email}: {str(e)}")

        # Process patients to delete
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