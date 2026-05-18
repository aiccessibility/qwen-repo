"""Analytics service for monitoring and trend analysis."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from app.models.audit import Audit
from app.models.monitor import Monitor


class AnalyticsService:
    """Service for analytics and trend monitoring."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_audit_statistics(self, days: int = 30) -> Dict:
        """Get audit statistics for the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total audits
        total_audits = self.db.query(Audit).filter(
            Audit.created_at >= cutoff_date
        ).count()
        
        # Audits by status
        status_breakdown = self.db.query(
            Audit.status, func.count(Audit.id)
        ).filter(
            Audit.created_at >= cutoff_date
        ).group_by(Audit.status).all()
        
        # Average progress by day
        daily_progress = self.db.query(
            extract('day', Audit.created_at).label('day'),
            func.avg(Audit.progress).label('avg_progress')
        ).filter(
            Audit.created_at >= cutoff_date
        ).group_by(
            extract('day', Audit.created_at)
        ).order_by('day').all()
        
        # Severity trends
        severity_data = self.db.query(
            Audit.created_at,
            Audit.severity_summary
        ).filter(
            Audit.created_at >= cutoff_date,
            Audit.severity_summary.isnot(None)
        ).order_by(Audit.created_at).all()
        
        # Calculate average violations by severity
        severity_totals = {'critical': 0, 'serious': 0, 'moderate': 0, 'minor': 0}
        severity_counts = {'critical': 0, 'serious': 0, 'moderate': 0, 'minor': 0}
        
        for _, summary in severity_data:
            if isinstance(summary, dict):
                for severity, count in summary.items():
                    if severity in severity_totals and isinstance(count, (int, float)):
                        severity_totals[severity] += count
                        severity_counts[severity] += 1
        
        avg_severity = {
            k: severity_totals[k] / max(severity_counts[k], 1) 
            for k in severity_totals
        }
        
        return {
            'total_audits': total_audits,
            'status_breakdown': {status: count for status, count in status_breakdown},
            'daily_progress': [{'day': int(row.day), 'avg_progress': float(row.avg_progress)} for row in daily_progress],
            'average_severity': avg_severity,
            'period_days': days
        }
    
    def get_violation_trends(self, days: int = 30) -> Dict:
        """Get violation trends over time."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get completed audits with violations
        audits = self.db.query(Audit).filter(
            Audit.created_at >= cutoff_date,
            Audit.status == 'completed',
            Audit.wcag_violations.isnot(None)
        ).order_by(Audit.created_at).all()
        
        trends = {
            'dates': [],
            'critical': [],
            'serious': [],
            'moderate': [],
            'minor': [],
            'total': []
        }
        
        for audit in audits:
            date_str = audit.created_at.strftime('%Y-%m-%d')
            
            # Skip if already have data for this date (or aggregate)
            if date_str not in trends['dates']:
                trends['dates'].append(date_str)
                trends['critical'].append(0)
                trends['serious'].append(0)
                trends['moderate'].append(0)
                trends['minor'].append(0)
                trends['total'].append(0)
            
            idx = trends['dates'].index(date_str)
            
            if isinstance(audit.severity_summary, dict):
                critical = audit.severity_summary.get('critical', 0)
                serious = audit.severity_summary.get('serious', 0)
                moderate = audit.severity_summary.get('moderate', 0)
                minor = audit.severity_summary.get('minor', 0)
                
                trends['critical'][idx] += critical if isinstance(critical, (int, float)) else 0
                trends['serious'][idx] += serious if isinstance(serious, (int, float)) else 0
                trends['moderate'][idx] += moderate if isinstance(moderate, (int, float)) else 0
                trends['minor'][idx] += minor if isinstance(minor, (int, float)) else 0
                trends['total'][idx] += sum([
                    critical if isinstance(critical, (int, float)) else 0,
                    serious if isinstance(serious, (int, float)) else 0,
                    moderate if isinstance(moderate, (int, float)) else 0,
                    minor if isinstance(minor, (int, float)) else 0
                ])
        
        return trends
    
    def get_monitored_sites_status(self) -> List[Dict]:
        """Get status of all monitored sites."""
        monitors = self.db.query(Monitor).filter(Monitor.active == True).all()
        
        results = []
        for monitor in monitors:
            # Get last audit for this monitor
            last_audit = self.db.query(Audit).filter(
                Audit.url == monitor.url
            ).order_by(Audit.created_at.desc()).first()
            
            results.append({
                'id': monitor.id,
                'name': monitor.name,
                'url': monitor.url,
                'frequency_hours': monitor.frequency_hours,
                'active': monitor.active,
                'last_audit': {
                    'id': last_audit.id if last_audit else None,
                    'status': last_audit.status if last_audit else None,
                    'created_at': last_audit.created_at.isoformat() if last_audit else None,
                    'violations_count': len(last_audit.wcag_violations) if last_audit and last_audit.wcag_violations else 0
                } if last_audit else None
            })
        
        return results
    
    def get_compliance_score_history(self, days: int = 30) -> Dict:
        """Calculate compliance score trends over time."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        audits = self.db.query(Audit).filter(
            Audit.created_at >= cutoff_date,
            Audit.status == 'completed'
        ).order_by(Audit.created_at).all()
        
        scores = []
        dates = []
        
        for audit in audits:
            date_str = audit.created_at.strftime('%Y-%m-%d %H:%M')
            
            # Calculate compliance score (inverse of violations weighted by severity)
            if isinstance(audit.severity_summary, dict):
                critical = audit.severity_summary.get('critical', 0) or 0
                serious = audit.severity_summary.get('serious', 0) or 0
                moderate = audit.severity_summary.get('moderate', 0) or 0
                minor = audit.severity_summary.get('minor', 0) or 0
                
                # Weighted penalty
                penalty = (critical * 10) + (serious * 5) + (moderate * 2) + (minor * 1)
                score = max(0, 100 - penalty)
            else:
                score = 100
            
            scores.append(score)
            dates.append(date_str)
        
        return {
            'dates': dates,
            'scores': scores,
            'average_score': sum(scores) / max(len(scores), 1)
        }
    
    def get_realtime_metrics(self) -> Dict:
        """Get real-time metrics for dashboard."""
        # Active audits
        active_audits = self.db.query(Audit).filter(
            Audit.status.in_(['pending', 'queued', 'scanning', 'analyzing'])
        ).all()
        
        # Recent completed audits
        recent_completed = self.db.query(Audit).filter(
            Audit.status == 'completed'
        ).order_by(Audit.created_at.desc()).limit(10).all()
        
        # Queue stats
        queued_count = self.db.query(Audit).filter(
            Audit.status == 'queued'
        ).count()
        
        return {
            'active_audits_count': len(active_audits),
            'active_audits': [
                {
                    'id': a.id,
                    'url': a.url,
                    'status': a.status,
                    'progress': a.progress,
                    'created_at': a.created_at.isoformat()
                } for a in active_audits
            ],
            'queued_count': queued_count,
            'recent_completed': [
                {
                    'id': a.id,
                    'url': a.url,
                    'violations_count': len(a.wcag_violations) if a.wcag_violations else 0,
                    'completed_at': a.completed_at.isoformat() if a.completed_at else None
                } for a in recent_completed
            ]
        }
