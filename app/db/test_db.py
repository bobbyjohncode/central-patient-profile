from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base  # Updated import to use the base with all models

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # Use static pool for in-memory database
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_test_db():
    """Initialize test database with all tables."""
    # Import all models to ensure they are registered with SQLAlchemy
    from app.models.patient import Patient  # noqa
    Base.metadata.create_all(bind=engine)

def drop_test_db():
    Base.metadata.drop_all(bind=engine)

def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close() 