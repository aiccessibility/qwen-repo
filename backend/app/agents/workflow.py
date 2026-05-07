from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import uuid

from app.services.playwright_scanner import PlaywrightScanner
from app.services.report_generator import ReportGenerator


class AuditState(TypedDict):
    """State for the accessibility audit workflow."""
    url: str
    html_content: str
    screenshots: List[str]
    wcag_violations: List[Dict[str, Any]]
    severity_summary: Dict[str, int]
    recommendations: List[Dict[str, Any]]
    report_url: Optional[str]
    report_paths: Optional[Dict[str, str]]
    status: str
    created_at: datetime
    updated_at: datetime
    report_id: str
    scan_data: Optional[Dict[str, Any]]
    error: Optional[str]


class AuditorAgent:
    """Agent responsible for scanning and analyzing web pages for WCAG compliance."""
    
    def __init__(self, llm_model: str = "llama2:70b"):
        self.llm_model = llm_model
        self.llm = ChatOllama(
            model=llm_model,
            base_url="http://ollama:11434",
            temperature=0.1,
            format="json"
        )
        self.scanner = PlaywrightScanner(headless=True)
        self.parser = JsonOutputParser()
        
        # Prompt for analyzing violations
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert web accessibility auditor specializing in WCAG 2.1/2.2 guidelines.
Your task is to analyze HTML content and accessibility data to identify WCAG violations.

Analyze the provided data and return a JSON object with the following structure:
{{
    "violations": [
        {{
            "title": "Brief title of the violation",
            "description": "Detailed description of the issue",
            "severity": "critical|serious|moderate|minor",
            "level": "A|AA|AAA",
            "criterion": "WCAG criterion number (e.g., 1.1.1)",
            "element": "HTML element or selector",
            "recommendation": "How to fix this issue",
            "code_example": "Example of corrected code (optional)"
        }}
    ],
    "severity_summary": {{
        "critical": <number>,
        "serious": <number>,
        "moderate": <number>,
        "minor": <number>
    }}
}}

Be thorough but focus on actual violations. Prioritize issues that impact users with disabilities."""),
            ("human", """Here is the accessibility data to analyze:

Page Metadata: {metadata}

ARIA Information: {aria_info}

Quick Issues Detected: {quick_issues}

HTML Snippet (first 5000 chars): {html_snippet}

Accessibility Tree: {aria_tree}

Please analyze this data and identify all WCAG violations.""")
        ])
    
    async def scan_page(self, state: AuditState) -> AuditState:
        """Scan the webpage and extract content for analysis."""
        try:
            state["status"] = "scanning"
            state["updated_at"] = datetime.utcnow()
            
            # Initialize scanner if needed
            await self.scanner.start()
            
            # Scan the page
            scan_result = await self.scanner.scan_page(state["url"])
            
            if "error" in scan_result:
                state["error"] = scan_result["error"]
                state["status"] = "error"
                return state
            
            # Store scan data
            state["scan_data"] = scan_result
            state["html_content"] = scan_result.get("html_content", "")
            state["screenshots"] = [scan_result.get("screenshot")] if scan_result.get("screenshot") else []
            state["status"] = "scanned"
            state["updated_at"] = datetime.utcnow()
            
        except Exception as e:
            state["error"] = str(e)
            state["status"] = "error"
        
        return state
    
    async def analyze_violations(self, state: AuditState) -> AuditState:
        """Analyze the scanned content for WCAG violations using LLM."""
        try:
            state["status"] = "analyzing"
            state["updated_at"] = datetime.utcnow()
            
            if not state.get("scan_data"):
                state["error"] = "No scan data available"
                state["status"] = "error"
                return state
            
            scan_data = state["scan_data"]
            
            # Prepare data for LLM
            metadata = scan_data.get("metadata", {})
            aria_info = scan_data.get("aria_info", {})
            quick_issues = scan_data.get("quick_issues", [])
            html_snippet = scan_data.get("html_content", "")[:5000]
            aria_tree = scan_data.get("aria_tree", [])
            
            # Format prompt
            prompt = self.analysis_prompt.format(
                metadata=json.dumps(metadata, indent=2),
                aria_info=json.dumps(aria_info, indent=2),
                quick_issues=json.dumps(quick_issues, indent=2),
                html_snippet=html_snippet,
                aria_tree=json.dumps(aria_tree[:50], indent=2)  # Limit tree size
            )
            
            # Invoke LLM
            response = await self.llm.ainvoke(prompt)
            content = response.content
            
            # Parse JSON response
            try:
                # Extract JSON from response if wrapped in markdown
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                result = json.loads(content.strip())
                
                state["wcag_violations"] = result.get("violations", [])
                state["severity_summary"] = result.get("severity_summary", {
                    "critical": 0,
                    "serious": 0,
                    "moderate": 0,
                    "minor": 0
                })
                
            except json.JSONDecodeError as e:
                state["error"] = f"Failed to parse LLM response: {str(e)}"
                state["wcag_violations"] = []
                state["severity_summary"] = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
            
            state["status"] = "analyzed"
            state["updated_at"] = datetime.utcnow()
            
        except Exception as e:
            state["error"] = str(e)
            state["status"] = "error"
            state["wcag_violations"] = []
            state["severity_summary"] = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        
        return state
    
    async def generate_recommendations(self, state: AuditState) -> AuditState:
        """Generate fix recommendations for each violation."""
        try:
            state["status"] = "generating_recommendations"
            state["updated_at"] = datetime.utcnow()
            
            violations = state.get("wcag_violations", [])
            recommendations = []
            
            # Generate prioritized recommendations
            priority_order = {"critical": 1, "serious": 2, "moderate": 3, "minor": 4}
            
            for i, violation in enumerate(violations[:20]):  # Limit to top 20
                severity = violation.get("severity", "moderate")
                
                # Determine effort and impact
                effort = "Medium"
                if "alt" in violation.get("title", "").lower() or "label" in violation.get("title", "").lower():
                    effort = "Low"
                elif "structure" in violation.get("title", "").lower() or "landmark" in violation.get("title", "").lower():
                    effort = "High"
                
                impact = "High" if severity in ["critical", "serious"] else "Medium"
                
                recommendations.append({
                    "priority": f"P{i+1}",
                    "issue": violation.get("title", "Unknown issue"),
                    "effort": effort,
                    "impact": impact,
                    "severity": severity,
                    "wcag_criterion": violation.get("criterion", ""),
                    "fix_description": violation.get("recommendation", "")
                })
            
            # Sort by severity
            recommendations.sort(key=lambda x: priority_order.get(x.get("severity", "moderate"), 3))
            
            state["recommendations"] = recommendations
            state["status"] = "recommendations_generated"
            state["updated_at"] = datetime.utcnow()
            
        except Exception as e:
            state["error"] = str(e)
            state["status"] = "error"
        
        return state


class MonitorAgent:
    """Agent responsible for continuous monitoring of accessibility over time."""
    
    def __init__(self, llm_model: str = "llama2:13b"):
        self.llm_model = llm_model
        self.llm = ChatOllama(
            model=llm_model,
            base_url="http://ollama:11434",
            temperature=0.1
        )
        self.scanner = PlaywrightScanner(headless=True)
    
    async def check_changes(self, state: AuditState) -> AuditState:
        """Compare current state with previous audits to detect changes."""
        try:
            state["status"] = "checking_changes"
            state["updated_at"] = datetime.utcnow()
            
            # Re-scan the page to get current state
            await self.scanner.start()
            current_scan = await self.scanner.scan_page(state["url"])
            
            if "error" in current_scan:
                state["error"] = current_scan["error"]
                state["status"] = "error"
                return state
            
            # Compare with previous scan data if available
            previous_scan = state.get("scan_data", {})
            
            if previous_scan:
                # Simple comparison - can be enhanced with more sophisticated diffing
                prev_issues = len(previous_scan.get("quick_issues", []))
                curr_issues = len(current_scan.get("quick_issues", []))
                
                state["changes_detected"] = {
                    "previous_issue_count": prev_issues,
                    "current_issue_count": curr_issues,
                    "difference": curr_issues - prev_issues,
                    "regression": curr_issues > prev_issues
                }
            
            # Update scan data
            state["scan_data"] = current_scan
            state["status"] = "changes_checked"
            state["updated_at"] = datetime.utcnow()
            
        except Exception as e:
            state["error"] = str(e)
            state["status"] = "error"
        
        return state
    
    async def alert_if_needed(self, state: AuditState) -> AuditState:
        """Send alerts if critical regressions are detected."""
        try:
            state["status"] = "alerting"
            state["updated_at"] = datetime.utcnow()
            
            changes = state.get("changes_detected", {})
            
            if changes.get("regression", False):
                # Critical regression detected
                state["alert"] = {
                    "type": "regression",
                    "severity": "high" if changes.get("difference", 0) > 5 else "medium",
                    "message": f"Accessibility regression detected: {changes.get('difference')} new issues found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                state["alert"] = None
            
            state["status"] = "alert_checked"
            state["updated_at"] = datetime.utcnow()
            
        except Exception as e:
            state["error"] = str(e)
            state["status"] = "error"
        
        return state


class ReporterAgent:
    """Agent responsible for generating comprehensive accessibility reports."""
    
    def __init__(self, llm_model: str = "llama2:70b"):
        self.llm_model = llm_model
        self.generator = ReportGenerator(output_dir="/app/reports")
    
    async def generate_report(self, state: AuditState) -> AuditState:
        """Generate a detailed accessibility report in multiple formats."""
        try:
            state["status"] = "generating_report"
            state["updated_at"] = datetime.utcnow()
            
            # Prepare audit data for report generation
            scan_data = state.get("scan_data", {})
            
            audit_data = {
                "report_id": state.get("report_id", str(uuid.uuid4())),
                "url": state["url"],
                "metadata": scan_data.get("metadata", {}),
                "scanned_at": scan_data.get("scanned_at", datetime.utcnow().isoformat()),
                "status_code": scan_data.get("status_code"),
                "screenshot": scan_data.get("screenshot"),
                "aria_info": scan_data.get("aria_info", {}),
                "quick_issues": scan_data.get("quick_issues", []),
                "wcag_violations": state.get("wcag_violations", []),
                "severity_summary": state.get("severity_summary", {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}),
                "recommendations": state.get("recommendations", [])
            }
            
            # Generate reports in all formats
            report_paths = await self.generator.generate_all_formats(audit_data)
            
            state["report_paths"] = report_paths
            state["report_url"] = f"/reports/{audit_data['report_id']}"  # Base URL
            state["status"] = "completed"
            state["updated_at"] = datetime.utcnow()
            
        except Exception as e:
            state["error"] = str(e)
            state["status"] = "error"
        
        return state


def create_audit_graph() -> StateGraph:
    """Create the LangGraph workflow for accessibility auditing."""
    
    # Initialize agents
    auditor = AuditorAgent(llm_model="llama2:70b")
    reporter = ReporterAgent(llm_model="llama2:70b")
    
    # Create the graph
    workflow = StateGraph(AuditState)
    
    # Add nodes
    workflow.add_node("scan_page", auditor.scan_page)
    workflow.add_node("analyze_violations", auditor.analyze_violations)
    workflow.add_node("generate_recommendations", auditor.generate_recommendations)
    workflow.add_node("generate_report", reporter.generate_report)
    
    # Define edges
    workflow.set_entry_point("scan_page")
    workflow.add_edge("scan_page", "analyze_violations")
    workflow.add_edge("analyze_violations", "generate_recommendations")
    workflow.add_edge("generate_recommendations", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()


def create_monitor_graph() -> StateGraph:
    """Create the LangGraph workflow for continuous monitoring."""
    
    # Initialize agents
    monitor = MonitorAgent(llm_model="llama2:13b")
    reporter = ReporterAgent(llm_model="llama2:70b")
    
    # Create the graph
    workflow = StateGraph(AuditState)
    
    # Add nodes
    workflow.add_node("check_changes", monitor.check_changes)
    workflow.add_node("alert_if_needed", monitor.alert_if_needed)
    workflow.add_node("generate_report", reporter.generate_report)
    
    # Define edges
    workflow.set_entry_point("check_changes")
    workflow.add_edge("check_changes", "alert_if_needed")
    
    # Conditional edge based on alert status
    def should_generate_report(state: AuditState) -> str:
        if state.get("error"):
            return END
        return "generate_report"
    
    workflow.add_conditional_edges(
        "alert_if_needed",
        should_generate_report,
        ["generate_report", END]
    )
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()
