"""Audit model for storing accessibility audit results."""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.db.database import Base


class Audit(Base):
    """Audit table for storing accessibility audit results."""
    
    __tablename__ = "audits"
    
    id = Column(String(255), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Optional for anonymous audits
    url = Column(String(2048), nullable=False)
    wcag_level = Column(String(10), default="AA")
    wcag_version = Column(String(10), default="2.2")
    status = Column(String(50), default="pending")  # pending, queued, scanning, analyzing, completed, failed
    progress = Column(Integer, default=0)
    depth = Column(Integer, default=1)
    include_screenshots = Column(Boolean, default=True)
    
    # Celery task tracking
    celery_task_id = Column(String(255), nullable=True, index=True)
    
    # Content and results
    html_content = Column(Text)
    screenshots = Column(JSONB, default=list)
    wcag_violations = Column(JSONB, default=list)
    severity_summary = Column(JSONB, default=dict)
    recommendations = Column(JSONB, default=list)
    report_url = Column(String(2048))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Audit(id={self.id}, url={self.url}, status={self.status})>"
