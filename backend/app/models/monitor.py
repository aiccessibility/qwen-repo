"""Monitor model for continuous monitoring configurations."""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.database import Base


class Monitor(Base):
    """Monitor table for continuous monitoring configurations."""
    
    __tablename__ = "monitors"
    
    id = Column(String(255), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    url = Column(String(2048), nullable=False)
    schedule_cron = Column(String(100), default="0 0 * * *")  # Daily at midnight
    wcag_level = Column(String(10), default="AA")
    wcag_version = Column(String(10), default="2.2")
    status = Column(String(50), default="active")  # active, paused, stopped
    last_audit_at = Column(DateTime(timezone=True))
    next_audit_at = Column(DateTime(timezone=True), index=True)
    alert_email = Column(String(255))
    alert_webhook = Column(String(2048))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Monitor(id={self.id}, url={self.url}, status={self.status})>"
