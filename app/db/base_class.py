from sqlalchemy.orm import as_declarative
from sqlalchemy import Column, Integer

@as_declarative()
class Base:
    id = Column(Integer, primary_key=True, index=True)
    __name__: str
    
    # Generate __tablename__ automatically
    @classmethod
    def __tablename__(cls) -> str:
        return cls.__name__.lower() 