from datetime import date

def test_create_patient(client):
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "email": "john.doe@example.com",
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
    # First create a patient
    patient_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1992-02-02",
        "email": "jane.smith@example.com",
        "phone": "098-765-4321"
    }
    create_response = client.post("/patients/", json=patient_data)
    patient_id = create_response.json()["id"]

    # Then get the patient
    response = client.get(f"/patients/{patient_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == patient_data["first_name"]
    assert data["last_name"] == patient_data["last_name"]
    assert data["email"] == patient_data["email"]
    assert data["phone"] == patient_data["phone"]

def test_get_nonexistent_patient(client):
    response = client.get("/patients/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found"

def test_list_patients(client):
    # Create two patients
    patients = [
        {
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice@example.com"
        },
        {
            "first_name": "Bob",
            "last_name": "Brown",
            "email": "bob@example.com"
        }
    ]
    
    for patient in patients:
        client.post("/patients/", json=patient)

    # Get all patients
    response = client.get("/patients/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least our two patients
    assert any(p["first_name"] == "Alice" for p in data)
    assert any(p["first_name"] == "Bob" for p in data) 