"""WCAG Rule model for storing accessibility standards reference."""
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import VECTOR

from app.db.database import Base


class WCAGRule(Base):
    """WCAG rules reference table for semantic search."""
    
    __tablename__ = "wcag_rules"
    
    id = Column(String(50), primary_key=True)  # e.g., "1.1.1"
    version = Column(String(10), nullable=False)  # "2.1", "2.2"
    level = Column(String(10), nullable=False)  # "A", "AA", "AAA"
    principle = Column(String(100), nullable=False)  # "Perceivable", "Operable", etc.
    guideline = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    how_to_meet = Column(Text)
    embedding = Column(VECTOR(768))  # For semantic search with pgvector
    
    def __repr__(self):
        return f"<WCAGRule(id={self.id}, title={self.title})>"
