import pytest
from sqlalchemy import inspect
from app.db.init_db import init_db
from app.db.base_class import Base
from app.db.test_db import engine
from app.models.patient import Patient

def test_init_db():
    """Test that database initialization creates all required tables."""
    # Initialize the database
    init_db()
    
    # Get inspector to check tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # Verify that the patients table exists
    assert "patients" in tables
    
    # Verify that the table has all required columns
    columns = [col["name"] for col in inspector.get_columns("patients")]
    expected_columns = ["id", "first_name", "last_name", "date_of_birth", "email", "phone"]
    assert all(col in columns for col in expected_columns) 