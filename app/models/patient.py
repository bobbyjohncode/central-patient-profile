from sqlalchemy import Column, Integer, String, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
from app.db.base_class import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    date_of_birth = Column(Date)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    extensions = Column(MutableDict.as_mutable(JSON), default=dict)  # Store dynamic extension fields

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "email": self.email,
            "phone": self.phone,
            "extensions": self.extensions or {}
        }