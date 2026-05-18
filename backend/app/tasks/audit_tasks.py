"""
Celery tasks for accessibility audits.
"""
from celery import states
from datetime import datetime
import asyncio
from typing import Dict, Any

from app.celery_config import celery_app
from app.db.database import SessionLocal
from app.models.audit import Audit
from app.agents.workflow import create_audit_graph, create_monitor_graph, AuditState


@celery_app.task(
    bind=True,
    name='app.tasks.audit_tasks.run_audit_workflow_task',
    max_retries=3,
    default_retry_delay=300,
    track_started=True
)
def run_audit_workflow_task(
    self,
    audit_id: str,
    initial_state: Dict[str, Any]
):
    """
    Run the accessibility audit workflow as a Celery task.
    
    This task:
    1. Executes the LangGraph workflow for auditing
    2. Updates progress in database
    3. Handles retries on failure
    4. Persists results to PostgreSQL
    
    Args:
        audit_id: Unique identifier for the audit
        initial_state: Initial state dictionary for LangGraph workflow
    """
    db = SessionLocal()
    
    try:
        # Update status to processing
        db_audit = db.query(Audit).filter(Audit.id == audit_id).first()
        if db_audit:
            db_audit.status = "processing"
            db_audit.progress = 10
            db.commit()
        
        # Get the compiled workflow graph
        audit_graph = create_audit_graph()
        
        # Convert dict to AuditState if needed
        if isinstance(initial_state, dict):
            # Ensure all required fields are present
            required_fields = [
                'url', 'html_content', 'screenshots', 'wcag_violations',
                'severity_summary', 'recommendations', 'report_url', 
                'report_paths', 'status', 'created_at', 'updated_at',
                'report_id', 'scan_data', 'error', 'audit_id'
            ]
            for field in required_fields:
                if field not in initial_state:
                    if field == 'severity_summary':
                        initial_state[field] = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
                    elif field == 'created_at' or field == 'updated_at':
                        initial_state[field] = datetime.utcnow()
                    else:
                        initial_state[field] = None
        
        # Run the workflow asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(audit_graph.ainvoke(initial_state))
        finally:
            loop.close()
        
        # Update progress based on workflow stages
        update_progress(db, audit_id, 50, "analyzing")
        
        # Persist results to database
        db_audit = db.query(Audit).filter(Audit.id == audit_id).first()
        if db_audit:
            db_audit.status = result.get("status", "completed")
            db_audit.progress = 100 if result.get("status") == "completed" else 80
            db_audit.html_content = result.get("html_content", "")[:100000]  # Limit size
            db_audit.screenshots = result.get("screenshots", [])
            db_audit.wcag_violations = result.get("wcag_violations", [])
            db_audit.severity_summary = result.get("severity_summary", {})
            db_audit.recommendations = result.get("recommendations", [])
            db_audit.report_url = result.get("report_url")
            
            if result.get("status") == "completed":
                db_audit.completed_at = datetime.utcnow()
                update_progress(db, audit_id, 100, "completed")
            else:
                update_progress(db, audit_id, 90, "generating_report")
            
            db.commit()
        
        print(f"✅ Audit {audit_id} completed: {result.get('status')}")
        print(f"📊 Violations found: {len(result.get('wcag_violations', []))}")
        print(f"📄 Report paths: {result.get('report_paths')}")
        
        return {
            "audit_id": audit_id,
            "status": result.get("status"),
            "violations_count": len(result.get("wcag_violations", [])),
            "success": True
        }
        
    except Exception as exc:
        print(f"❌ Audit {audit_id} failed: {str(exc)}")
        
        # Update database with error
        db_audit = db.query(Audit).filter(Audit.id == audit_id).first()
        if db_audit:
            db_audit.status = "error"
            db_audit.error = str(exc)
            db_audit.progress = 0
            db.commit()
        
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes
        else:
            # Mark as failed permanently
            return {
                "audit_id": audit_id,
                "status": "error",
                "error": str(exc),
                "success": False
            }
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name='app.tasks.audit_tasks.run_monitor_workflow_task',
    max_retries=3,
    default_retry_delay=300,
    track_started=True
)
def run_monitor_workflow_task(
    self,
    monitor_id: str,
    initial_state: Dict[str, Any]
):
    """
    Run the continuous monitoring workflow as a Celery task.
    
    This task:
    1. Executes the LangGraph workflow for monitoring
    2. Detects changes and regressions
    3. Sends alerts for critical issues
    4. Schedules next monitoring cycle
    
    Args:
        monitor_id: Unique identifier for the monitor
        initial_state: Initial state dictionary for LangGraph workflow
    """
    from app.models.monitor import Monitor
    
    db = SessionLocal()
    
    try:
        # Update status
        db_monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        if db_monitor:
            db_monitor.status = "processing"
            db.commit()
        
        # Get the monitoring workflow
        monitor_graph = create_monitor_graph()
        
        # Run the workflow
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(monitor_graph.ainvoke(initial_state))
        finally:
            loop.close()
        
        # Check for alerts
        if result.get("alert"):
            alert_msg = f"🚨 ALERT: {result['alert']['message']}"
            print(alert_msg)
            # In production, send email/webhook notification here
        
        # Update database
        db_monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        if db_monitor:
            db_monitor.status = "active"
            db_monitor.last_check = datetime.utcnow()
            db.commit()
        
        print(f"✅ Monitor {monitor_id} completed: {result.get('status')}")
        
        # Schedule next monitoring cycle (e.g., every 24 hours)
        # run_monitor_workflow_task.apply_async(
        #     args=[monitor_id, initial_state],
        #     countdown=86400  # 24 hours
        # )
        
        return {
            "monitor_id": monitor_id,
            "status": result.get("status"),
            "alert": result.get("alert"),
            "success": True
        }
        
    except Exception as exc:
        print(f"❌ Monitor {monitor_id} failed: {str(exc)}")
        
        db_monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        if db_monitor:
            db_monitor.status = "error"
            db.commit()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=300)
        else:
            return {
                "monitor_id": monitor_id,
                "status": "error",
                "error": str(exc),
                "success": False
            }
    finally:
        db.close()


def update_progress(db, audit_id: str, progress: int, status: str):
    """Helper function to update audit progress in database."""
    db_audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if db_audit:
        db_audit.progress = progress
        db_audit.status = status
        db.commit()
