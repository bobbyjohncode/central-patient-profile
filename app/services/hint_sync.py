import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
import httpx
import logging
from app.schemas.patient import PatientCreate, PatientSyncRequest, PatientProfile
from app.core.config import settings, EXTENSION_FIELDS

# Set up logging
logger = logging.getLogger(__name__)

def extract_core_fields(hint_patient: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and validate required core fields from Hint patient data.
    
    Args:
        hint_patient: Raw patient data from Hint API
        
    Returns:
        Dict containing validated core fields
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    try:
        return {
            "first_name": hint_patient["first_name"],
            "last_name": hint_patient["last_name"],
            "email": hint_patient["email"],
            "date_of_birth": datetime.fromisoformat(hint_patient["date_of_birth"]).date(),
            "gender": hint_patient["gender"]
        }
    except KeyError as e:
        raise ValueError(f"Missing required field in Hint patient data: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid date format in Hint patient data: {e}")

def create_field_ownership(core_fields: Dict[str, Any]) -> Dict[str, str]:
    """Create field ownership mapping for core fields.
    
    Args:
        core_fields: Dict of core field names and values
        
    Returns:
        Dict mapping field names to source system
    """
    return {field: "hint" for field in core_fields.keys()}

def extract_address(hint_patient: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract address information from Hint patient data.
    
    Args:
        hint_patient: Raw patient data from Hint API
        
    Returns:
        Dict containing address fields
    """
    address = hint_patient.get("address", {})
    return {
        "street": address.get("street"),
        "city": address.get("city"),
        "state": address.get("state"),
        "zip_code": address.get("zip_code"),
        "country": address.get("country")
    }

def extract_insurance(hint_patient: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract insurance information from Hint patient data.
    
    Args:
        hint_patient: Raw patient data from Hint API
        
    Returns:
        Dict containing insurance fields
    """
    return {
        "provider": hint_patient.get("insurance_provider"),
        "policy_number": hint_patient.get("insurance_policy_number"),
        "group_number": hint_patient.get("insurance_group_number"),
        "plan_type": hint_patient.get("insurance_plan_type"),
        "coverage_start": hint_patient.get("insurance_coverage_start"),
        "coverage_end": hint_patient.get("insurance_coverage_end")
    }

def extract_emergency_contact(hint_patient: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract emergency contact information from Hint patient data.
    
    Args:
        hint_patient: Raw patient data from Hint API
        
    Returns:
        Dict containing emergency contact fields
    """
    contact = hint_patient.get("emergency_contact", {})
    return {
        "name": contact.get("name"),
        "relationship": contact.get("relationship"),
        "phone": contact.get("phone")
    }

def create_hint_extensions(hint_patient: Dict[str, Any]) -> Dict[str, Any]:
    """Create Hint-specific extension fields from patient data.
    
    Args:
        hint_patient: Raw patient data from Hint API
        
    Returns:
        Dict containing Hint extension fields
    """
    return {
        "hint": {
            # Practice information
            "practice_id": hint_patient.get("practice_id"),
            "patient_id": hint_patient.get("patient_id"),
            "membership_status": hint_patient.get("membership_status"),
            
            # Contact information
            "phone": hint_patient.get("phone"),
            "mobile_phone": hint_patient.get("mobile_phone"),
            "preferred_contact_method": hint_patient.get("preferred_contact_method"),
            "preferred_language": hint_patient.get("preferred_language"),
            
            # Structured information
            "address": extract_address(hint_patient),
            "insurance": extract_insurance(hint_patient),
            "emergency_contact": extract_emergency_contact(hint_patient),
            
            # Medical information
            "allergies": hint_patient.get("allergies", []),
            "medications": hint_patient.get("medications", []),
            "conditions": hint_patient.get("conditions", []),
            "immunizations": hint_patient.get("immunizations", []),
            
            # Visit information
            "last_visit_date": hint_patient.get("last_visit_date"),
            "next_appointment": hint_patient.get("next_appointment"),
            "visit_history": hint_patient.get("visit_history", []),
            
            # Additional information
            "notes": hint_patient.get("notes"),
            "preferences": hint_patient.get("preferences", {}),
            "consents": hint_patient.get("consents", {}),
            
            # Metadata
            "last_updated": hint_patient.get("last_updated"),
            "created_at": hint_patient.get("created_at"),
            "source_system": "hint"
        }
    }

def map_hint_patient_to_profile(hint_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map Hint patient data to our internal profile format.
    
    This function takes raw patient data from Hint and maps it to our internal
    profile format, which includes:
    - Core fields (name, dob, email, etc.)
    - Hint-specific fields in extensions["hint"]
    - Source system tracking for each field
    
    Args:
        hint_data: Raw patient data from Hint API
        
    Returns:
        Dict containing:
        - Core fields mapped directly
        - Non-core fields in extensions["hint"]
        - Source system tracking for each field
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Extract and validate required core fields
    try:
        core_fields = {
            "first_name": hint_data["first_name"],
            "last_name": hint_data["last_name"],
            "email": hint_data["email"],
            "date_of_birth": datetime.fromisoformat(hint_data["date_of_birth"]).date(),
            "gender": hint_data["gender"]
        }
    except KeyError as e:
        raise ValueError(f"Missing required field in Hint patient data: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid date format in Hint patient data: {e}")
    
    # Create source system tracking for core fields
    source_systems = {field: "hint" for field in core_fields.keys()}
    
    # Create Hint extensions with all non-core fields
    hint_extensions = create_hint_extensions(hint_data)
    
    # Check for missing required extension fields
    if "hint" in EXTENSION_FIELDS:
        hint_namespace = EXTENSION_FIELDS["hint"]
        for field_name in hint_namespace.required_fields:
            if field_name not in hint_extensions["hint"]:
                logger.warning(
                    f"Missing required Hint extension field: {field_name}",
                    extra={
                        "patient_id": hint_data.get("patient_id", "unknown"),
                        "field": field_name,
                        "namespace": "hint"
                    }
                )
    
    # Add source system tracking for extension fields
    for field in hint_extensions["hint"].keys():
        if field != "source_system":  # Skip the source_system field itself
            source_systems[f"extensions.hint.{field}"] = "hint"
    
    # Create the final profile structure
    profile = {
        **core_fields,
        "extensions": hint_extensions,
        "source_systems": source_systems,
        "source_system": "hint",
        "last_sync_at": datetime.utcnow().isoformat()
    }
    
    return profile

class HintSyncService:
    """Service for synchronizing patient data with Hint Practice API.
    
    This service handles:
    - Authentication with Hint API
    - Fetching patient data
    - Mapping Hint fields to internal schema
    - Error handling and retries
    - Rate limiting compliance
    """
    
    def __init__(self):
        """Initialize the Hint sync service.
        
        Raises:
            ValueError: If HINT_PRACTICE_API_KEY is not set in environment
        """
        self.api_key = os.getenv("HINT_PRACTICE_API_KEY")
        if not self.api_key:
            raise ValueError("HINT_PRACTICE_API_KEY environment variable is required")
            
        self.base_url = "https://api.hint.com/v1"  # Replace with actual Hint API URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    async def fetch_patients(self, last_sync: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch patients from Hint API.
        
        Args:
            last_sync: Optional timestamp to fetch only updated records
            
        Returns:
            List of patient records from Hint
            
        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If API response is invalid
        """
        params = {}
        if last_sync:
            params["updated_since"] = last_sync.isoformat()
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/patients",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                if not isinstance(data, list):
                    raise ValueError("Invalid API response format")
                    
                return data
                
            except httpx.HTTPError as e:
                if e.response and e.response.status_code == 401:
                    raise ValueError("Invalid Hint API key")
                raise
                
    def map_hint_patient(self, hint_patient: Dict[str, Any]) -> PatientCreate:
        """Map Hint patient data to internal schema.
        
        Args:
            hint_patient: Patient data from Hint API
            
        Returns:
            Mapped PatientCreate object
            
        Raises:
            ValueError: If required fields are missing
        """
        # Extract core fields
        try:
            return PatientCreate(
                first_name=hint_patient["first_name"],
                last_name=hint_patient["last_name"],
                email=hint_patient["email"],
                date_of_birth=datetime.fromisoformat(hint_patient["date_of_birth"]).date(),
                gender=hint_patient["gender"],
                
                # Map Hint-specific fields to extensions
                extensions={
                    "hint": {
                        "membership_status": hint_patient.get("membership_status"),
                        "practice_id": hint_patient.get("practice_id"),
                        "patient_id": hint_patient.get("patient_id"),
                        "insurance_provider": hint_patient.get("insurance_provider"),
                        "insurance_policy_number": hint_patient.get("insurance_policy_number"),
                        "last_visit_date": hint_patient.get("last_visit_date"),
                        "next_appointment": hint_patient.get("next_appointment"),
                        "preferred_contact_method": hint_patient.get("preferred_contact_method"),
                        "preferred_language": hint_patient.get("preferred_language"),
                        "emergency_contact": hint_patient.get("emergency_contact"),
                        "allergies": hint_patient.get("allergies", []),
                        "medications": hint_patient.get("medications", []),
                        "conditions": hint_patient.get("conditions", []),
                        "notes": hint_patient.get("notes")
                    }
                }
            )
        except KeyError as e:
            raise ValueError(f"Missing required field in Hint patient data: {e}")
            
    async def create_sync_request(self, last_sync: Optional[datetime] = None) -> PatientSyncRequest:
        """Create a sync request from Hint API data.
        
        Args:
            last_sync: Optional timestamp to fetch only updated records
            
        Returns:
            PatientSyncRequest with mapped patient data
            
        Raises:
            ValueError: If API request fails or data is invalid
        """
        hint_patients = await self.fetch_patients(last_sync)
        
        # Map all patients
        mapped_patients = []
        errors = []
        
        for hint_patient in hint_patients:
            try:
                mapped_patient = self.map_hint_patient(hint_patient)
                mapped_patients.append(mapped_patient)
            except ValueError as e:
                errors.append(f"Failed to map patient {hint_patient.get('patient_id')}: {str(e)}")
                
        return PatientSyncRequest(
            patients=mapped_patients,
            source_system="hint",
            delete_missing=True  # Delete patients that no longer exist in Hint
        )
        
    async def validate_api_connection(self) -> bool:
        """Validate the Hint API connection.
        
        Returns:
            True if connection is valid
            
        Raises:
            ValueError: If connection fails
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=self.headers,
                    timeout=5.0
                )
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                if e.response and e.response.status_code == 401:
                    raise ValueError("Invalid Hint API key")
                raise ValueError(f"Failed to connect to Hint API: {str(e)}")

    async def sync_patient_by_id(self, patient_id: str) -> Dict[str, Any]:
        """Fetch and map a single patient by ID from Hint API.
        
        This method:
        1. Fetches the patient data from Hint API
        2. Maps the data to our internal profile schema
        3. Returns the mapped profile
        
        Args:
            patient_id: Hint's patient ID
            
        Returns:
            Dict containing the mapped patient profile
            
        Raises:
            ValueError: If patient not found or required fields are missing
            httpx.HTTPError: If API request fails
        """
        async with httpx.AsyncClient() as client:
            try:
                # Fetch patient data
                response = await client.get(
                    f"{self.base_url}/patients/{patient_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                hint_patient = response.json()
                
                if not isinstance(hint_patient, dict):
                    raise ValueError("Invalid API response format")
                    
                # Map to our schema
                return map_hint_patient_to_profile(hint_patient)
                
            except httpx.HTTPError as e:
                if e.response and e.response.status_code == 404:
                    raise ValueError(f"Patient not found: {patient_id}")
                if e.response and e.response.status_code == 401:
                    raise ValueError("Invalid Hint API key")
                raise 