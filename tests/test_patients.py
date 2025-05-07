import pytest
from datetime import date
from fastapi import HTTPException

def test_create_patient(client):
    """Test creating a patient with valid data."""
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "email": "john.doe.test1@example.com",
        "phone": "123-456-7890"
    }
    
    response = client.post("/patients/", json=patient_data)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == patient_data["first_name"]
    assert data["last_name"] == patient_data["last_name"]
    assert data["email"] == patient_data["email"]
    assert data["phone"] == patient_data["phone"]
    assert "id" in data

def test_get_patient(client):
    """Test retrieving a specific patient."""
    patient_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1992-02-02",
        "email": "jane.smith.test3@example.com",
        "phone": "098-765-4321"
    }
    
    create_response = client.post("/patients/", json=patient_data)
    assert create_response.status_code == 200
    created_patient = create_response.json()
    
    response = client.get(f"/patients/{created_patient['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == patient_data["first_name"]
    assert data["last_name"] == patient_data["last_name"]
    assert data["email"] == patient_data["email"]

def test_get_nonexistent_patient(client):
    """Test retrieving a non-existent patient."""
    response = client.get("/patients/999")
    assert response.status_code == 404

def test_list_patients(client):
    """Test listing multiple patients."""
    patients = [
        {
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice.johnson.test4@example.com"
        },
        {
            "first_name": "Bob",
            "last_name": "Brown",
            "email": "bob.brown.test4@example.com"
        }
    ]
    
    for patient in patients:
        client.post("/patients/", json=patient)
    
    response = client.get("/patients/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_list_patients_empty(client):
    """Test listing patients when the database is empty."""
    response = client.get("/patients/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

def test_sync_patients(client):
    """Test the complete sync workflow: create, update, and delete patients."""
    # Create initial patients
    initial_patients = [
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe.test5@example.com"
        },
        {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith.test5@example.com"
        }
    ]
    
    for patient in initial_patients:
        client.post("/patients/", json=patient)
    
    # Prepare sync data (update one, add one, remove one)
    sync_data = {
        "patients": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe.updated.test5@example.com"  # Updated email
            },
            {
                "first_name": "New",
                "last_name": "Patient",
                "email": "new.patient.test5@example.com"  # New patient
            }
        ]
    }
    
    # Perform sync
    response = client.post("/patients/sync", json=sync_data)
    assert response.status_code == 200
    data = response.json()
    
    # Verify sync results
    assert "synced" in data
    assert "created" in data
    assert "updated" in data
    assert "deleted" in data
    
    # Get all patients to verify final state
    response = client.get("/patients/")
    assert response.status_code == 200
    final_patients = response.json()
    
    # Should have 2 patients (John updated, New added, Jane removed)
    assert len(final_patients) == 2
    
    # Verify the updated patient
    updated_patient = next(p for p in final_patients if p["email"] == "john.doe.updated.test5@example.com")
    assert updated_patient["first_name"] == "John"
    assert updated_patient["last_name"] == "Doe"
    
    # Verify the new patient
    new_patient = next(p for p in final_patients if p["email"] == "new.patient.test5@example.com")
    assert new_patient["first_name"] == "New"
    assert new_patient["last_name"] == "Patient"

def test_sync_patients_empty(client):
    """Test syncing with an empty list of patients."""
    sync_data = {"patients": []}
    response = client.post("/patients/sync", json=sync_data)
    assert response.status_code == 200
    data = response.json()
    assert data["synced"] == 0
    assert data["created"] == 0
    assert data["updated"] == 0
    assert data["deleted"] == 0

def test_create_patient_with_extensions(client):
    """Test creating a patient with extension fields."""
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "email": "john.doe.ext@example.com",
        "phone": "123-456-7890",
        "extensions": {
            "epic": {
                "external_id": "ABC12345",
                "last_visit_date": "2024-03-15"
            },
            "cerner": {
                "mrn": "1234567890",
                "is_active": True
            }
        }
    }
    
    response = client.post("/patients/", json=patient_data)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == patient_data["first_name"]
    assert data["email"] == patient_data["email"]
    assert "extensions" in data
    assert data["extensions"]["epic"]["external_id"] == "ABC12345"
    assert data["extensions"]["cerner"]["mrn"] == "1234567890"

def test_create_patient_invalid_extension(client):
    """Test creating a patient with invalid extension field."""
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe.invalid@example.com",
        "extensions": {
            "epic": {
                "external_id": "invalid"  # Invalid format
            }
        }
    }
    
    response = client.post("/patients/", json=patient_data)
    assert response.status_code == 400
    assert "Invalid value for extension field" in response.json()["detail"]

def test_update_patient_extensions(client):
    """Test updating a patient's extension fields."""
    # First create a patient
    patient_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith.ext@example.com",
        "extensions": {
            "epic": {
                "external_id": "DEF67890"
            }
        }
    }
    
    create_response = client.post("/patients/", json=patient_data)
    assert create_response.status_code == 200
    created_patient = create_response.json()
    
    # Update the patient with new extensions
    update_data = {
        "extensions": {
            "epic": {
                "external_id": "DEF67890",
                "last_visit_date": "2024-03-20"
            },
            "cerner": {
                "mrn": "0987654321",
                "is_active": True
            }
        }
    }
    
    response = client.put(f"/patients/{created_patient['id']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert "extensions" in data
    assert data["extensions"]["epic"]["last_visit_date"] == "2024-03-20"
    assert data["extensions"]["cerner"]["mrn"] == "0987654321"

def test_sync_patients_with_extensions(client):
    """Test syncing patients with extension fields."""
    # Create initial patients
    initial_patients = [
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe.sync@example.com",
            "extensions": {
                "epic": {"external_id": "ABC12345"}
            }
        },
        {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith.sync@example.com",
            "extensions": {
                "cerner": {
                    "mrn": "1234567890",
                    "is_active": True
                }
            }
        }
    ]
    
    # Create initial patients and check responses
    for patient in initial_patients:
        response = client.post("/patients/", json=patient)
        print(f"Creating patient {patient['email']}: status={response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.json()}")
        assert response.status_code == 200, f"Failed to create patient {patient['email']}: {response.json()}"
    
    # Verify initial patients exist
    list_response = client.get("/patients/")
    assert list_response.status_code == 200
    initial_list = list_response.json()
    print(f"Initial patients: {[p['email'] for p in initial_list]}")
    assert len(initial_list) == 2, "Expected 2 initial patients"

    # Prepare sync data
    sync_data = {
        "patients": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe.sync@example.com",
                "extensions": {
                    "epic": {
                        "external_id": "ABC12345",
                        "last_visit_date": "2024-03-25"
                    }
                }
            },
            {
                "first_name": "New",
                "last_name": "Patient",
                "email": "new.patient.sync@example.com",
                "extensions": {
                    "allscripts": {
                        "insurance_provider": "AETNA"
                    }
                }
            }
        ]
    }
    
    response = client.post("/patients/sync", json=sync_data)
    assert response.status_code == 200
    data = response.json()
    assert data["synced"] == 2
    assert data["created"] == 1
    assert data["updated"] == 1
    assert data["deleted"] == 1 