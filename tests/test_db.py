import os
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import get_db, get_database_url
from app.models.patient import Patient

def test_get_db_session():
    """Test that get_db yields a valid session and closes it properly."""
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    assert isinstance(db, Session)
    
    # Test that the session is closed after use
    try:
        next(db_gen)
    except StopIteration:
        pass
    
    # Verify session is closed by trying to execute a query
    with pytest.raises(SQLAlchemyError):
        db.query(Patient).first()

def test_database_url_validation():
    """Test that the application validates DATABASE_URL."""
    # Save original DATABASE_URL
    original_url = os.environ.get("DATABASE_URL")
    
    try:
        # Test with empty string
        os.environ["DATABASE_URL"] = ""
        with pytest.raises(ValueError, match="DATABASE_URL environment variable is not set"):
            get_database_url()
        
        # Test with None
        del os.environ["DATABASE_URL"]
        with pytest.raises(ValueError, match="DATABASE_URL environment variable is not set"):
            get_database_url()
            
    finally:
        # Restore original DATABASE_URL
        if original_url:
            os.environ["DATABASE_URL"] = original_url 