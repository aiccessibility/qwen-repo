from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
import uuid
from datetime import datetime

from app.agents.workflow import create_audit_graph, AuditState
from app.utils.config import settings
from app.db.database import get_db
from app.models.audit import Audit
from app.tasks.audit_tasks import run_audit_workflow_task, run_monitor_workflow_task


router = APIRouter()


class AuditRequest(BaseModel):
    """Request model for initiating an accessibility audit."""
    url: str
    wcag_level: Optional[str] = "AA"
    wcag_version: Optional[str] = "2.2"
    include_screenshots: Optional[bool] = True
    depth: Optional[int] = 1  # Number of pages to audit


class AuditResponse(BaseModel):
    """Response model for audit requests."""
    audit_id: str
    status: str
    url: str
    message: str


class AuditStatusResponse(BaseModel):
    """Response model for audit status checks."""
    audit_id: str
    status: str
    progress: int
    violations_count: Optional[int] = None
    severity_summary: Optional[dict] = None
    report_url: Optional[str] = None
    error: Optional[str] = None


@router.post("/audit", response_model=AuditResponse, tags=["Auditing"])
async def start_audit(
    request: AuditRequest,
    db: Session = Depends(get_db)
):
    """
    Start a new accessibility audit for a given URL.
    
    The audit will:
    1. Scan the webpage and extract HTML/CSS/JS
    2. Analyze for WCAG violations using AI agents
    3. Generate recommendations for fixes
    4. Create a comprehensive report (PDF, HTML, JSON)
    
    Results are available via the status endpoint or webhook.
    The audit runs asynchronously in a Celery worker queue.
    """
    # Generate unique audit ID
    audit_id = str(uuid.uuid4())
    
    # Create audit record in database
    db_audit = Audit(
        id=audit_id,
        url=request.url,
        wcag_level=request.wcag_level or "AA",
        wcag_version=request.wcag_version or "2.2",
        depth=request.depth or 1,
        include_screenshots=request.include_screenshots or True,
        status="pending",
        progress=0,
    )
    db.add(db_audit)
    db.commit()
    
    # Initialize audit state for LangGraph workflow
    initial_state: AuditState = {
        "url": request.url,
        "html_content": "",
        "screenshots": [],
        "wcag_violations": [],
        "severity_summary": {"critical": 0, "serious": 0, "moderate": 0, "minor": 0},
        "recommendations": [],
        "report_url": None,
        "report_paths": None,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "report_id": audit_id,
        "scan_data": None,
        "error": None,
        "audit_id": audit_id,  # Pass audit_id to workflow
    }
    
    # Queue the audit task in Celery
    task = run_audit_workflow_task.delay(audit_id, initial_state)
    
    # Store task ID for tracking
    db_audit.celery_task_id = task.id
    db.commit()
    
    return AuditResponse(
        audit_id=audit_id,
        status="queued",
        url=request.url,
        message=f"Audit queued successfully. Task ID: {task.id}. Check status with GET /audit/{audit_id}"
    )



@router.get("/audit/{audit_id}", response_model=AuditStatusResponse, tags=["Auditing"])
async def get_audit_status(audit_id: str, db: Session = Depends(get_db)):
    """
    Get the status of an ongoing or completed audit.
    
    Returns current progress and preliminary results if available.
    Now uses database as primary source since Celery handles execution.
    """
    # Query database for audit status
    db_audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not db_audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    # Calculate progress based on status
    status_progress = {
        "pending": 0,
        "queued": 5,
        "scanning": 20,
        "scanned": 30,
        "analyzing": 50,
        "analyzed": 60,
        "generating_recommendations": 70,
        "recommendations_generated": 80,
        "generating_report": 90,
        "completed": 100,
        "error": 0
    }
    
    progress = status_progress.get(db_audit.status, db_audit.progress)
    
    return AuditStatusResponse(
        audit_id=audit_id,
        status=db_audit.status,
        progress=progress,
        violations_count=len(db_audit.wcag_violations or []),
        severity_summary=db_audit.severity_summary,
        report_url=db_audit.report_url,
        error=db_audit.error
    )


@router.get("/audit/{audit_id}/report", tags=["Auditing"])
async def get_audit_report(audit_id: str, format: Optional[str] = "json", db: Session = Depends(get_db)):
    """
    Download the complete audit report in various formats.
    
    Supported formats: json, pdf, html
    """
    # Query database for audit
    db_audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not db_audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    if db_audit.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not ready yet. Current status: {db_audit.status}"
        )
    
    # Build report paths from storage directory
    import os
    from app.utils.config import settings
    
    storage_dir = settings.STORAGE_DIR or "/app/storage"
    report_paths = {
        "json": os.path.join(storage_dir, "reports", f"{audit_id}.json"),
        "html": os.path.join(storage_dir, "reports", f"{audit_id}.html"),
        "pdf": os.path.join(storage_dir, "reports", f"{audit_id}.pdf"),
    }
    
    format_lower = format.lower()
    
    if format_lower == "json":
        file_path = report_paths.get("json")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="JSON report not found")
        return FileResponse(file_path, media_type="application/json", filename=f"audit_{audit_id}.json")
    
    elif format_lower == "html":
        file_path = report_paths.get("html")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="HTML report not found")
        return FileResponse(file_path, media_type="text/html", filename=f"audit_{audit_id}.html")
    
    elif format_lower == "pdf":
        file_path = report_paths.get("pdf")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF report not found")
        return FileResponse(file_path, media_type="application/pdf", filename=f"audit_{audit_id}.pdf")
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: json, pdf, html"
        )


@router.get("/audit/{audit_id}/results", tags=["Auditing"])
async def get_audit_results(audit_id: str, db: Session = Depends(get_db)):
    """
    Get the full audit results as JSON.
    """
    # Query database
    db_audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not db_audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    if db_audit.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Results not ready yet. Current status: {db_audit.status}"
        )
    
    return {
        "audit_id": audit_id,
        "url": db_audit.url,
        "status": db_audit.status,
        "severity_summary": db_audit.severity_summary or {},
        "wcag_violations": db_audit.wcag_violations or [],
        "recommendations": db_audit.recommendations or [],
        "completed_at": db_audit.completed_at.isoformat() if db_audit.completed_at else None
    }


@router.post("/monitor", response_model=AuditResponse, tags=["Monitoring"])
async def start_monitoring(
    request: AuditRequest,
    db: Session = Depends(get_db)
):
    """
    Start continuous monitoring for a URL.
    
    The system will:
    1. Perform initial audit
    2. Schedule periodic re-audits
    3. Detect changes and regressions
    4. Send alerts for critical issues
    
    Monitoring continues until explicitly stopped.
    """
    from app.agents.workflow import create_monitor_graph
    from app.models.monitor import Monitor
    
    monitor_id = str(uuid.uuid4())
    
    # Create monitor record in database
    db_monitor = Monitor(
        id=monitor_id,
        url=request.url,
        wcag_level=request.wcag_level or "AA",
        wcag_version=request.wcag_version or "2.2",
        status="active",
    )
    db.add(db_monitor)
    db.commit()
    
    # Initialize monitor state
    initial_state: AuditState = {
        "url": request.url,
        "html_content": "",
        "screenshots": [],
        "wcag_violations": [],
        "severity_summary": {"critical": 0, "serious": 0, "moderate": 0, "minor": 0},
        "recommendations": [],
        "report_url": None,
        "report_paths": None,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "report_id": monitor_id,
        "scan_data": None,
        "error": None,
        "audit_id": monitor_id,
    }
    
    # Queue the monitoring task in Celery
    task = run_monitor_workflow_task.delay(monitor_id, initial_state)
    
    # Store task ID for tracking
    db_monitor.celery_task_id = task.id
    db.commit()
    
    return AuditResponse(
        audit_id=monitor_id,
        status="queued",
        url=request.url,
        message=f"Monitoring queued. Task ID: {task.id}. Initial audit in progress."
    )


@router.delete("/monitor/{monitor_id}", tags=["Monitoring"])
async def stop_monitoring(monitor_id: str, db: Session = Depends(get_db)):
    """Stop continuous monitoring for a URL."""
    from app.models.monitor import Monitor
    
    db_monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not db_monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    db_monitor.status = "stopped"
    db.commit()
    
    return {"message": f"Monitoring {monitor_id} stopped successfully"}


@router.get("/wcag/rules", tags=["WCAG Standards"])
async def get_wcag_rules(
    level: Optional[str] = "AA",
    version: Optional[str] = "2.2"
):
    """
    Get the list of WCAG rules used for auditing.
    
    Returns detailed information about each success criterion.
    """
    # Sample WCAG rules - in production, load from vector DB
    return {
        "version": version,
        "level": level,
        "rules": [
            {
                "id": "1.1.1",
                "name": "Non-text Content",
                "level": "A",
                "principle": "Perceivable",
                "description": "All non-text content has a text alternative"
            },
            {
                "id": "1.3.1",
                "name": "Info and Relationships",
                "level": "A",
                "principle": "Perceivable",
                "description": "Information, structure, and relationships can be programmatically determined"
            },
            {
                "id": "2.4.4",
                "name": "Link Purpose (In Context)",
                "level": "A",
                "principle": "Operable",
                "description": "The purpose of each link can be determined from the link text alone"
            },
            {
                "id": "3.1.1",
                "name": "Language of Page",
                "level": "A",
                "principle": "Understandable",
                "description": "The default human language of each page can be programmatically determined"
            }
        ],
        "total_rules": 50
    }
