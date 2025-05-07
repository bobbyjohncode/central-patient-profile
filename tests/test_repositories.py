import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreate, PatientUpdate, PatientSyncRequest
from app.models.patient import Patient

@pytest_asyncio.fixture
async def repository(db: AsyncSession) -> PatientRepository:
    """Get a repository instance with a test database session."""
    return PatientRepository(db)

@pytest.mark.asyncio
async def test_create_patient(repository: PatientRepository):
    """Test creating a new patient."""
    patient_data = PatientCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        date_of_birth="1990-01-01",
        gender="male",
        extensions={
            "cerner": {
                "mrn": "12345",
                "is_active": True
            }
        }
    )
    
    patient = await repository.create(patient_data)
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"
    assert patient.email == "john.doe@example.com"
    assert patient.extensions["cerner"]["mrn"] == "12345"

@pytest.mark.asyncio
async def test_get_patient(repository: PatientRepository):
    """Test getting a patient by ID."""
    # Create a test patient
    patient_data = PatientCreate(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        date_of_birth="1992-02-02",
        gender="female"
    )
    created_patient = await repository.create(patient_data)
    
    # Get the patient
    patient = await repository.get(created_patient.id)
    assert patient is not None
    assert patient.email == "jane.smith@example.com"
    
    # Test non-existent patient
    non_existent = await repository.get(999)
    assert non_existent is None

@pytest.mark.asyncio
async def test_get_patient_by_email(repository: PatientRepository):
    """Test getting a patient by email."""
    # Create a test patient
    patient_data = PatientCreate(
        first_name="Bob",
        last_name="Johnson",
        email="bob.johnson@example.com",
        date_of_birth="1985-03-03",
        gender="male"
    )
    await repository.create(patient_data)
    
    # Get the patient
    patient = await repository.get_by_email("bob.johnson@example.com")
    assert patient is not None
    assert patient.first_name == "Bob"
    
    # Test non-existent email
    non_existent = await repository.get_by_email("nonexistent@example.com")
    assert non_existent is None

@pytest.mark.asyncio
async def test_list_patients(repository: PatientRepository):
    """Test listing patients with pagination."""
    # Create multiple test patients
    patients = [
        PatientCreate(
            first_name=f"User{i}",
            last_name=f"Test{i}",
            email=f"user{i}@example.com",
            date_of_birth="1990-01-01",
            gender="male"
        )
        for i in range(5)
    ]
    
    for patient_data in patients:
        await repository.create(patient_data)
    
    # Test default pagination
    all_patients = await repository.list()
    assert len(all_patients) == 5
    
    # Test with limit
    limited_patients = await repository.list(limit=2)
    assert len(limited_patients) == 2
    
    # Test with skip
    skipped_patients = await repository.list(skip=2)
    assert len(skipped_patients) == 3

@pytest.mark.asyncio
async def test_update_patient(repository: PatientRepository):
    """Test updating a patient."""
    # Create a test patient
    patient_data = PatientCreate(
        first_name="Alice",
        last_name="Brown",
        email="alice.brown@example.com",
        date_of_birth="1995-04-04",
        gender="female"
    )
    created_patient = await repository.create(patient_data)
    
    # Update the patient
    update_data = PatientUpdate(
        first_name="Alice Updated",
        extensions={
            "cerner": {
                "mrn": "67890",
                "is_active": True
            }
        }
    )
    updated_patient = await repository.update(created_patient.id, update_data)
    assert updated_patient is not None
    assert updated_patient.first_name == "Alice Updated"
    assert updated_patient.extensions["cerner"]["mrn"] == "67890"
    
    # Test updating non-existent patient
    non_existent = await repository.update(999, update_data)
    assert non_existent is None

@pytest.mark.asyncio
async def test_delete_patient(repository: PatientRepository):
    """Test deleting a patient."""
    # Create a test patient
    patient_data = PatientCreate(
        first_name="Charlie",
        last_name="Davis",
        email="charlie.davis@example.com",
        date_of_birth="1988-05-05",
        gender="male"
    )
    created_patient = await repository.create(patient_data)
    
    # Delete the patient
    success = await repository.delete(created_patient.id)
    assert success is True
    
    # Verify patient is deleted
    deleted_patient = await repository.get(created_patient.id)
    assert deleted_patient is None
    
    # Test deleting non-existent patient
    non_existent = await repository.delete(999)
    assert non_existent is False

@pytest.mark.asyncio
async def test_sync_patients(repository: PatientRepository):
    """Test syncing patients."""
    # Create initial patients
    initial_patients = [
        PatientCreate(
            first_name=f"Initial{i}",
            last_name=f"User{i}",
            email=f"initial{i}@example.com",
            date_of_birth="1990-01-01",
            gender="male"
        )
        for i in range(3)
    ]
    
    for patient_data in initial_patients:
        await repository.create(patient_data)
    
    # Create sync request
    sync_data = PatientSyncRequest(
        patients=[
            PatientCreate(
                first_name="New",
                last_name="Patient",
                email="new@example.com",
                date_of_birth="1995-01-01",
                gender="female"
            ),
            PatientCreate(
                first_name="Initial0",
                last_name="User0 Updated",
                email="initial0@example.com",
                date_of_birth="1990-01-01",
                gender="male"
            )
        ],
        delete_missing=True
    )
    
    # Perform sync
    result = await repository.sync_patients(sync_data)
    
    assert result["created"] == 1
    assert result["updated"] == 1
    assert result["deleted"] == 2  # initial1 and initial2 should be deleted
    assert len(result["errors"]) == 0
    
    # Verify final state
    all_patients = await repository.list()
    assert len(all_patients) == 2
    
    # Verify updated patient
    updated_patient = await repository.get_by_email("initial0@example.com")
    assert updated_patient.last_name == "User0 Updated"
    
    # Verify new patient
    new_patient = await repository.get_by_email("new@example.com")
    assert new_patient is not None
    assert new_patient.first_name == "New" 