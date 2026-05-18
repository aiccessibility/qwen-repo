"""Analytics API endpoints for dashboard and monitoring."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/statistics")
def get_audit_statistics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get audit statistics for the last N days."""
    analytics = AnalyticsService(db)
    return analytics.get_audit_statistics(days=days)


@router.get("/trends/violations")
def get_violation_trends(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get violation trends over time."""
    analytics = AnalyticsService(db)
    return analytics.get_violation_trends(days=days)


@router.get("/trends/compliance")
def get_compliance_score_history(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get compliance score history over time."""
    analytics = AnalyticsService(db)
    return analytics.get_compliance_score_history(days=days)


@router.get("/monitors/status")
def get_monitored_sites_status(db: Session = Depends(get_db)):
    """Get status of all monitored sites."""
    analytics = AnalyticsService(db)
    return analytics.get_monitored_sites_status()


@router.get("/realtime")
def get_realtime_metrics(db: Session = Depends(get_db)):
    """Get real-time metrics for dashboard."""
    analytics = AnalyticsService(db)
    return analytics.get_realtime_metrics()
