from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from app.models.patient import Patient

class TrustScoreCalculator:
    """Calculates trust scores for patient profiles based on data quality and freshness.
    
    The trust score is a weighted average of multiple factors that indicate the
    reliability and completeness of a patient's data. This helps identify profiles
    that may need attention or updates.
    
    Score Components:
    - Field Completeness (30%): Required fields present and valid
    - Data Freshness (20%): How recently the data was synced
    - Extension Completeness (30%): Required extension fields present
    - Field Ownership (20%): Clear ownership of core fields
    
    The final score ranges from 0-100, where:
    - 90-100: Excellent data quality
    - 70-89: Good data quality
    - 50-69: Fair data quality
    - 0-49: Poor data quality
    """
    
    def __init__(self):
        """Initialize the trust score calculator with required fields and weights."""
        self.required_fields = ['first_name', 'last_name', 'email', 'date_of_birth']
        self.max_sync_age_days = 30
        self.weights: List[float] = [0.3, 0.2, 0.3, 0.2]  # Field, Freshness, Extension, Ownership
    
    def calculate_score(self, patient: Patient) -> int:
        """Calculate the overall trust score for a patient profile.
        
        Args:
            patient: The patient record to evaluate
            
        Returns:
            Integer score from 0-100 representing data quality
        """
        scores = [
            self._calculate_field_score(patient),
            self._calculate_freshness_score(patient),
            self._calculate_extension_score(patient),
            self._calculate_ownership_score(patient)
        ]
        
        final_score = sum(score * weight for score, weight in zip(scores, self.weights))
        return int(final_score)
    
    def _calculate_field_score(self, patient: Patient) -> int:
        """Calculate score based on required field completeness.
        
        Args:
            patient: The patient record to evaluate
            
        Returns:
            Integer score from 0-100 for field completeness
        """
        present_fields = sum(1 for field in self.required_fields 
                           if getattr(patient, field) is not None)
        return (present_fields / len(self.required_fields)) * 100
    
    def _calculate_freshness_score(self, patient: Patient) -> int:
        """Calculate score based on data freshness.
        
        Args:
            patient: The patient record to evaluate
            
        Returns:
            Integer score from 0-100 for data freshness
        """
        if not patient.last_sync_at:
            return 0
        
        days_since_sync = (datetime.now() - patient.last_sync_at).days
        if days_since_sync > self.max_sync_age_days:
            return 0
        
        return int((1 - (days_since_sync / self.max_sync_age_days)) * 100)
    
    def _calculate_extension_score(self, patient: Patient) -> int:
        """Calculate score based on extension field completeness.
        
        Args:
            patient: The patient record to evaluate
            
        Returns:
            Integer score from 0-100 for extension completeness
        """
        if not patient.extensions:
            return 0
        
        total_fields = 0
        filled_fields = 0
        
        for namespace, fields in patient.extensions.items():
            for field, value in fields.items():
                total_fields += 1
                if value is not None and value != "":
                    filled_fields += 1
        
        return int((filled_fields / total_fields) * 100) if total_fields > 0 else 0
    
    def _calculate_ownership_score(self, patient: Patient) -> int:
        """Calculate score based on field ownership clarity.
        
        Args:
            patient: The patient record to evaluate
            
        Returns:
            Integer score from 0-100 for field ownership clarity
        """
        if not patient.field_ownership:
            return 0
        
        total_fields = len(self.required_fields)
        owned_fields = sum(1 for field in self.required_fields 
                          if field in patient.field_ownership)
        
        return int((owned_fields / total_fields) * 100)
    
    def get_score_breakdown(self, patient: Patient) -> Dict[str, Tuple[int, float]]:
        """Get detailed breakdown of trust score components.
        
        Args:
            patient: The patient record to evaluate
            
        Returns:
            Dict mapping component names to (score, weight) tuples
        """
        return {
            "field_completeness": (self._calculate_field_score(patient), self.weights[0]),
            "data_freshness": (self._calculate_freshness_score(patient), self.weights[1]),
            "extension_completeness": (self._calculate_extension_score(patient), self.weights[2]),
            "field_ownership": (self._calculate_ownership_score(patient), self.weights[3])
        } 