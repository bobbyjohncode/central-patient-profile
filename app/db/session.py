import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get and validate database URL from environment variable."""
    url = os.getenv("DATABASE_URL")
    if not url or url.strip() == "":
        raise ValueError("DATABASE_URL environment variable is not set")
    return url

# Get database URL from environment variable
DATABASE_URL = get_database_url()

# Create engine without the check_same_thread parameter (not needed for Postgres)
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
