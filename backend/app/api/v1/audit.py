from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Response
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
import uuid
from datetime import datetime

from app.agents.workflow import create_audit_graph, AuditState
from app.utils.config import settings


router = APIRouter()

# In-memory store for audit states (replace with database in production)
audit_store = {}


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
    background_tasks: BackgroundTasks
):
    """
    Start a new accessibility audit for a given URL.
    
    The audit will:
    1. Scan the webpage and extract HTML/CSS/JS
    2. Analyze for WCAG violations using AI agents
    3. Generate recommendations for fixes
    4. Create a comprehensive report (PDF, HTML, JSON)
    
    Results are available via the status endpoint or webhook.
    """
    # Generate unique audit ID
    audit_id = str(uuid.uuid4())
    
    # Initialize audit state
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
    }
    
    # Store initial state
    audit_store[audit_id] = initial_state
    
    # Get the compiled workflow graph
    audit_graph = create_audit_graph()
    
    # Run the workflow in background
    background_tasks.add_task(run_audit_workflow, audit_id, initial_state, audit_graph)
    
    return AuditResponse(
        audit_id=audit_id,
        status="pending",
        url=request.url,
        message="Audit started successfully. Check status with GET /audit/{audit_id}"
    )


async def run_audit_workflow(audit_id: str, initial_state: AuditState, graph):
    """Run the audit workflow asynchronously."""
    try:
        # Update status to processing
        audit_store[audit_id]["status"] = "processing"
        
        # Execute the LangGraph workflow
        result = await graph.ainvoke(initial_state)
        
        # Store results
        audit_store[audit_id] = result
        
        print(f"Audit {audit_id} completed: {result.get('status')}")
        print(f"Violations found: {len(result.get('wcag_violations', []))}")
        print(f"Report paths: {result.get('report_paths')}")
        
    except Exception as e:
        print(f"Audit {audit_id} failed: {str(e)}")
        audit_store[audit_id]["status"] = "error"
        audit_store[audit_id]["error"] = str(e)


@router.get("/audit/{audit_id}", response_model=AuditStatusResponse, tags=["Auditing"])
async def get_audit_status(audit_id: str):
    """
    Get the status of an ongoing or completed audit.
    
    Returns current progress and preliminary results if available.
    """
    if audit_id not in audit_store:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    state = audit_store[audit_id]
    
    # Calculate progress based on status
    status_progress = {
        "pending": 0,
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
    
    progress = status_progress.get(state.get("status", "pending"), 0)
    
    return AuditStatusResponse(
        audit_id=audit_id,
        status=state.get("status", "unknown"),
        progress=progress,
        violations_count=len(state.get("wcag_violations", [])),
        severity_summary=state.get("severity_summary"),
        report_url=state.get("report_url"),
        error=state.get("error")
    )


@router.get("/audit/{audit_id}/report", tags=["Auditing"])
async def get_audit_report(audit_id: str, format: Optional[str] = "json"):
    """
    Download the complete audit report in various formats.
    
    Supported formats: json, pdf, html
    """
    if audit_id not in audit_store:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    state = audit_store[audit_id]
    
    if state.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not ready yet. Current status: {state.get('status')}"
        )
    
    report_paths = state.get("report_paths", {})
    
    if not report_paths:
        raise HTTPException(status_code=404, detail="Report files not found")
    
    format_lower = format.lower()
    
    if format_lower == "json":
        file_path = report_paths.get("json")
        if not file_path:
            raise HTTPException(status_code=404, detail="JSON report not found")
        return FileResponse(file_path, media_type="application/json", filename=f"audit_{audit_id}.json")
    
    elif format_lower == "html":
        file_path = report_paths.get("html")
        if not file_path:
            raise HTTPException(status_code=404, detail="HTML report not found")
        return FileResponse(file_path, media_type="text/html", filename=f"audit_{audit_id}.html")
    
    elif format_lower == "pdf":
        file_path = report_paths.get("pdf")
        if not file_path:
            raise HTTPException(status_code=404, detail="PDF report not found")
        return FileResponse(file_path, media_type="application/pdf", filename=f"audit_{audit_id}.pdf")
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: json, pdf, html"
        )


@router.get("/audit/{audit_id}/results", tags=["Auditing"])
async def get_audit_results(audit_id: str):
    """
    Get the full audit results as JSON.
    """
    if audit_id not in audit_store:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    state = audit_store[audit_id]
    
    if state.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Results not ready yet. Current status: {state.get('status')}"
        )
    
    return {
        "audit_id": audit_id,
        "url": state.get("url"),
        "status": state.get("status"),
        "scanned_at": state.get("scan_data", {}).get("scanned_at"),
        "metadata": state.get("scan_data", {}).get("metadata", {}),
        "severity_summary": state.get("severity_summary", {}),
        "wcag_violations": state.get("wcag_violations", []),
        "quick_issues": state.get("scan_data", {}).get("quick_issues", []),
        "recommendations": state.get("recommendations", []),
        "aria_info": state.get("scan_data", {}).get("aria_info", {}),
        "report_paths": state.get("report_paths")
    }


@router.post("/monitor", response_model=AuditResponse, tags=["Monitoring"])
async def start_monitoring(
    request: AuditRequest,
    background_tasks: BackgroundTasks
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
    
    monitor_id = str(uuid.uuid4())
    
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
    }
    
    # Store initial state
    audit_store[monitor_id] = initial_state
    
    # Get the monitoring workflow
    monitor_graph = create_monitor_graph()
    
    # Run the workflow in background
    background_tasks.add_task(run_monitor_workflow, monitor_id, initial_state, monitor_graph)
    
    return AuditResponse(
        audit_id=monitor_id,
        status="active",
        url=request.url,
        message="Monitoring started. Initial audit in progress."
    )


async def run_monitor_workflow(monitor_id: str, initial_state: AuditState, graph):
    """Run the monitoring workflow asynchronously."""
    try:
        audit_store[monitor_id]["status"] = "processing"
        result = await graph.ainvoke(initial_state)
        audit_store[monitor_id] = result
        
        # Check for alerts
        if result.get("alert"):
            print(f"🚨 ALERT: {result['alert']['message']}")
        
        print(f"Monitor {monitor_id} completed: {result.get('status')}")
        
    except Exception as e:
        print(f"Monitor {monitor_id} failed: {str(e)}")
        audit_store[monitor_id]["status"] = "error"
        audit_store[monitor_id]["error"] = str(e)


@router.delete("/monitor/{monitor_id}", tags=["Monitoring"])
async def stop_monitoring(monitor_id: str):
    """Stop continuous monitoring for a URL."""
    if monitor_id not in audit_store:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    # In production, update database and stop scheduled tasks
    audit_store[monitor_id]["status"] = "stopped"
    
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
