import pytest
from datetime import datetime, date
from app.services.hint_sync import map_hint_patient_to_profile
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import hmac
import hashlib
import os

@pytest.fixture
def sample_hint_patient():
    """Sample Hint patient data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "practice_id": "HINT12345",
        "patient_id": "P123456789012",
        "membership_status": "active",
        "phone": "5551234567",
        "mobile_phone": "5559876543",
        "preferred_contact_method": "email",
        "preferred_language": "en",
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "country": "USA"
        },
        "insurance": {
            "provider": "Blue Cross",
            "policy_number": "BC123456",
            "group_number": "GRP789",
            "plan_type": "PPO",
            "coverage_start": "2023-01-01",
            "coverage_end": "2023-12-31"
        },
        "allergies": ["Penicillin", "Peanuts"],
        "medications": [
            {
                "name": "Lisinopril",
                "dosage": "10mg",
                "frequency": "daily"
            }
        ],
        "conditions": ["Hypertension"],
        "immunizations": [
            {
                "vaccine": "COVID-19",
                "date": "2023-01-15"
            }
        ],
        "last_visit_date": "2023-12-01",
        "next_appointment": "2024-03-15",
        "visit_history": [
            {
                "date": "2023-12-01",
                "provider": "Dr. Smith",
                "reason": "Annual checkup",
                "notes": "Patient is doing well"
            }
        ],
        "emergency_contact": {
            "name": "Jane Doe",
            "relationship": "Spouse",
            "phone": "5551112222"
        },
        "notes": "Patient prefers morning appointments",
        "preferences": {
            "appointment_reminders": "email",
            "communication_preference": "email"
        },
        "consents": {
            "hipaa": {
                "signed": True,
                "date": "2023-01-01"
            },
            "financial": {
                "signed": True,
                "date": "2023-01-01"
            }
        },
        "last_updated": "2024-01-15T10:30:00Z",
        "created_at": "2023-01-01T08:00:00Z"
    }

def test_map_hint_patient_to_profile_core_fields(sample_hint_patient):
    """Test that core fields are correctly mapped."""
    profile = map_hint_patient_to_profile(sample_hint_patient)
    
    # Verify core fields
    assert profile["first_name"] == "John"
    assert profile["last_name"] == "Doe"
    assert profile["email"] == "john.doe@example.com"
    assert profile["date_of_birth"] == date(1990, 1, 1)
    assert profile["gender"] == "male"
    
    # Verify source system tracking
    assert profile["source_systems"]["first_name"] == "hint"
    assert profile["source_systems"]["last_name"] == "hint"
    assert profile["source_systems"]["email"] == "hint"
    assert profile["source_systems"]["date_of_birth"] == "hint"
    assert profile["source_systems"]["gender"] == "hint"

def test_map_hint_patient_to_profile_extensions(sample_hint_patient):
    """Test that Hint-specific fields are correctly mapped to extensions."""
    profile = map_hint_patient_to_profile(sample_hint_patient)
    hint_extensions = profile["extensions"]["hint"]
    
    # Verify practice information
    assert hint_extensions["practice_id"] == "HINT12345"
    assert hint_extensions["patient_id"] == "P123456789012"
    assert hint_extensions["membership_status"] == "active"
    
    # Verify contact information
    assert hint_extensions["phone"] == "5551234567"
    assert hint_extensions["mobile_phone"] == "5559876543"
    assert hint_extensions["preferred_contact_method"] == "email"
    assert hint_extensions["preferred_language"] == "en"
    
    # Verify address
    assert hint_extensions["address"]["street"] == "123 Main St"
    assert hint_extensions["address"]["city"] == "Anytown"
    assert hint_extensions["address"]["state"] == "CA"
    assert hint_extensions["address"]["zip_code"] == "12345"
    assert hint_extensions["address"]["country"] == "USA"
    
    # Verify insurance
    assert hint_extensions["insurance"]["provider"] == "Blue Cross"
    assert hint_extensions["insurance"]["policy_number"] == "BC123456"
    assert hint_extensions["insurance"]["group_number"] == "GRP789"
    assert hint_extensions["insurance"]["plan_type"] == "PPO"
    assert hint_extensions["insurance"]["coverage_start"] == "2023-01-01"
    assert hint_extensions["insurance"]["coverage_end"] == "2023-12-31"
    
    # Verify medical information
    assert hint_extensions["allergies"] == ["Penicillin", "Peanuts"]
    assert len(hint_extensions["medications"]) == 1
    assert hint_extensions["medications"][0]["name"] == "Lisinopril"
    assert hint_extensions["medications"][0]["dosage"] == "10mg"
    assert hint_extensions["medications"][0]["frequency"] == "daily"
    assert hint_extensions["conditions"] == ["Hypertension"]
    assert len(hint_extensions["immunizations"]) == 1
    assert hint_extensions["immunizations"][0]["vaccine"] == "COVID-19"
    assert hint_extensions["immunizations"][0]["date"] == "2023-01-15"
    
    # Verify visit information
    assert hint_extensions["last_visit_date"] == "2023-12-01"
    assert hint_extensions["next_appointment"] == "2024-03-15"
    assert len(hint_extensions["visit_history"]) == 1
    assert hint_extensions["visit_history"][0]["date"] == "2023-12-01"
    assert hint_extensions["visit_history"][0]["provider"] == "Dr. Smith"
    assert hint_extensions["visit_history"][0]["reason"] == "Annual checkup"
    assert hint_extensions["visit_history"][0]["notes"] == "Patient is doing well"
    
    # Verify emergency contact
    assert hint_extensions["emergency_contact"]["name"] == "Jane Doe"
    assert hint_extensions["emergency_contact"]["relationship"] == "Spouse"
    assert hint_extensions["emergency_contact"]["phone"] == "5551112222"
    
    # Verify consents
    assert hint_extensions["consents"]["hipaa"]["signed"] is True
    assert hint_extensions["consents"]["hipaa"]["date"] == "2023-01-01"
    assert hint_extensions["consents"]["financial"]["signed"] is True
    assert hint_extensions["consents"]["financial"]["date"] == "2023-01-01"

def test_map_hint_patient_to_profile_metadata(sample_hint_patient):
    """Test that source system metadata is correctly set."""
    profile = map_hint_patient_to_profile(sample_hint_patient)
    
    # Verify source system
    assert profile["source_system"] == "hint"
    assert "last_sync_at" in profile
    assert isinstance(profile["last_sync_at"], str)
    
    # Verify extension metadata
    assert profile["extensions"]["hint"]["last_updated"] == "2024-01-15T10:30:00Z"
    assert profile["extensions"]["hint"]["created_at"] == "2023-01-01T08:00:00Z"
    assert profile["extensions"]["hint"]["source_system"] == "hint"

def test_map_hint_patient_to_profile_missing_required_fields():
    """Test that missing required fields raise an error."""
    patient = {
        "first_name": "John",
        "last_name": "Doe",
        # Missing email
        "date_of_birth": "1990-01-01",
        "gender": "male"
    }
    
    with pytest.raises(ValueError, match="Missing required field in Hint patient data: 'email'"):
        map_hint_patient_to_profile(patient)

def test_map_hint_patient_to_profile_invalid_date():
    """Test that invalid date formats raise an error."""
    patient = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "date_of_birth": "invalid-date",  # Invalid date format
        "gender": "male"
    }
    
    with pytest.raises(ValueError, match="Invalid date format in Hint patient data"):
        map_hint_patient_to_profile(patient)

def test_map_hint_patient_to_profile_optional_fields():
    """Test that optional fields are handled correctly."""
    patient = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "date_of_birth": "1990-01-01",
        "gender": "male"
        # No optional fields provided
    }
    
    profile = map_hint_patient_to_profile(patient)
    hint_extensions = profile["extensions"]["hint"]
    
    # Verify optional fields are None or empty
    assert hint_extensions["phone"] is None
    assert hint_extensions["mobile_phone"] is None
    assert hint_extensions["address"] == {
        "street": None,
        "city": None,
        "state": None,
        "zip_code": None,
        "country": None
    }
    assert hint_extensions["allergies"] == []
    assert hint_extensions["medications"] == []
    assert hint_extensions["conditions"] == []
    assert hint_extensions["immunizations"] == []
    assert hint_extensions["visit_history"] == []

@pytest.fixture
def test_client():
    """Create a test client for FastAPI."""
    return TestClient(app)

@pytest.fixture
def webhook_secret():
    """Set up webhook secret for testing."""
    secret = "test_webhook_secret"
    os.environ["HINT_WEBHOOK_SECRET"] = secret
    return secret

@pytest.fixture
def webhook_payload():
    """Sample webhook payload for patient.updated event."""
    return {
        "event_type": "patient.updated",
        "patient_id": "P123456789012",
        "timestamp": "2024-03-15T10:30:00Z",
        "data": {
            "changes": {
                "email": "john.doe.updated@example.com",
                "phone": "5551234567"
            }
        }
    }

def test_hint_webhook_handling(test_client, webhook_secret, webhook_payload):
    """Test that the Hint webhook endpoint correctly processes patient update events."""
    # Calculate webhook signature
    body = test_client.json.dumps(webhook_payload).encode()
    signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Mock the HintSyncService to avoid actual API calls
    with patch("app.services.hint_sync.HintSyncService") as mock_service:
        # Configure the mock
        mock_instance = mock_service.return_value
        mock_instance.sync_patient_by_id = AsyncMock()
        
        # Make the webhook request
        response = test_client.post(
            "/webhooks/hint",
            json=webhook_payload,
            headers={"X-Hint-Signature": signature}
        )
        
        # Verify response
        assert response.status_code == 202
        assert response.json() == {
            "status": "accepted",
            "message": "Processing patient.updated for patient P123456789012"
        }
        
        # Verify sync was triggered
        mock_instance.sync_patient_by_id.assert_called_once_with("P123456789012")

def test_hint_webhook_invalid_signature(test_client, webhook_payload):
    """Test that webhook requests with invalid signatures are rejected."""
    # Make request with invalid signature
    response = test_client.post(
        "/webhooks/hint",
        json=webhook_payload,
        headers={"X-Hint-Signature": "invalid_signature"}
    )
    
    # Verify response
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature"

def test_hint_webhook_missing_signature(test_client, webhook_payload):
    """Test that webhook requests without signatures are rejected."""
    # Make request without signature
    response = test_client.post(
        "/webhooks/hint",
        json=webhook_payload
    )
    
    # Verify response
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing webhook signature"

def test_hint_webhook_invalid_event_type(test_client, webhook_secret, webhook_payload):
    """Test that webhook requests with invalid event types are rejected."""
    # Modify payload with invalid event type
    invalid_payload = webhook_payload.copy()
    invalid_payload["event_type"] = "invalid.event"
    
    # Calculate signature for invalid payload
    body = test_client.json.dumps(invalid_payload).encode()
    signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Make request with invalid event type
    response = test_client.post(
        "/webhooks/hint",
        json=invalid_payload,
        headers={"X-Hint-Signature": signature}
    )
    
    # Verify response
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid event type"

def test_hint_webhook_invalid_payload(test_client, webhook_secret):
    """Test that webhook requests with invalid payloads are rejected."""
    # Create invalid payload (missing required fields)
    invalid_payload = {
        "event_type": "patient.updated",
        # Missing patient_id
        "timestamp": "2024-03-15T10:30:00Z"
    }
    
    # Calculate signature for invalid payload
    body = test_client.json.dumps(invalid_payload).encode()
    signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Make request with invalid payload
    response = test_client.post(
        "/webhooks/hint",
        json=invalid_payload,
        headers={"X-Hint-Signature": signature}
    )
    
    # Verify response
    assert response.status_code == 400
    assert "Invalid webhook payload" in response.json()["detail"] 