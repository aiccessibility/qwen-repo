"""
Report generation service for creating PDF and HTML accessibility reports.
"""
import os
import aiofiles
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import base64
import io


class ReportGenerator:
    """Service for generating accessibility reports in multiple formats."""
    
    def __init__(self, output_dir: str = "/app/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5282'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#2b6cb0'),
            spaceAfter=8,
            spaceBefore=8
        ))
    
    async def generate_html_report(self, audit_data: Dict[str, Any]) -> str:
        """Generate an HTML report from audit data."""
        
        template = Template('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Audit Report - {{ metadata.title }}</title>
    <style>
        :root {
            --primary: #1a365d;
            --secondary: #2c5282;
            --accent: #3182ce;
            --critical: #e53e3e;
            --serious: #dd6b20;
            --moderate: #d69e2e;
            --minor: #38a169;
            --bg-light: #f7fafc;
            --border: #e2e8f0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #2d3748;
            background: var(--bg-light);
            padding: 2rem;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 3rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        header {
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 3px solid var(--primary);
        }
        
        h1 {
            color: var(--primary);
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: #718096;
            font-size: 1.1rem;
        }
        
        .meta-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--bg-light);
            border-radius: 6px;
        }
        
        .meta-item {
            display: flex;
            flex-direction: column;
        }
        
        .meta-label {
            font-weight: 600;
            color: #4a5568;
            font-size: 0.875rem;
        }
        
        .meta-value {
            color: #2d3748;
            font-size: 1rem;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .card {
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            border: 2px solid var(--border);
        }
        
        .card.critical { border-color: var(--critical); background: #fff5f5; }
        .card.serious { border-color: var(--serious); background: #fffaf0; }
        .card.moderate { border-color: var(--moderate); background: #fffff0; }
        .card.minor { border-color: var(--minor); background: #f0fff4; }
        
        .card-number {
            font-size: 3rem;
            font-weight: bold;
            display: block;
        }
        
        .card.critical .card-number { color: var(--critical); }
        .card.serious .card-number { color: var(--serious); }
        .card.moderate .card-number { color: var(--moderate); }
        .card.minor .card-number { color: var(--minor); }
        
        .card-label {
            font-size: 0.875rem;
            color: #4a5568;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        section {
            margin: 3rem 0;
        }
        
        h2 {
            color: var(--secondary);
            font-size: 1.75rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--border);
        }
        
        h3 {
            color: var(--accent);
            font-size: 1.25rem;
            margin: 1.5rem 0 1rem;
        }
        
        .issue {
            background: white;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .issue-title {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .severity-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .severity-critical { background: var(--critical); color: white; }
        .severity-serious { background: var(--serious); color: white; }
        .severity-moderate { background: var(--moderate); color: white; }
        .severity-minor { background: var(--minor); color: white; }
        
        .issue-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .detail-item {
            background: var(--bg-light);
            padding: 0.75rem;
            border-radius: 4px;
        }
        
        .detail-label {
            font-size: 0.75rem;
            color: #718096;
            text-transform: uppercase;
        }
        
        .detail-value {
            font-size: 0.875rem;
            color: #2d3748;
            word-break: break-all;
        }
        
        .recommendation {
            background: #ebf8ff;
            border-left: 4px solid var(--accent);
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 4px 4px 0;
        }
        
        .recommendation-title {
            font-weight: 600;
            color: var(--secondary);
            margin-bottom: 0.5rem;
        }
        
        .code-block {
            background: #1a202c;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            margin: 1rem 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        
        th {
            background: var(--bg-light);
            font-weight: 600;
            color: #4a5568;
        }
        
        footer {
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 2px solid var(--border);
            text-align: center;
            color: #718096;
            font-size: 0.875rem;
        }
        
        .screenshot {
            max-width: 100%;
            height: auto;
            border: 1px solid var(--border);
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        @media print {
            body {
                background: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
                padding: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>♿ Accessibility Audit Report</h1>
            <p class="subtitle">{{ metadata.title or 'Unknown Page' }}</p>
        </header>
        
        <div class="meta-info">
            <div class="meta-item">
                <span class="meta-label">URL</span>
                <span class="meta-value">{{ metadata.url or 'N/A' }}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Audit Date</span>
                <span class="meta-value">{{ scanned_at }}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Language</span>
                <span class="meta-value">{{ metadata.lang or 'Not specified' }}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Status Code</span>
                <span class="meta-value">{{ status_code or 'N/A' }}</span>
            </div>
        </div>
        
        <h2>Executive Summary</h2>
        <div class="summary-cards">
            <div class="card critical">
                <span class="card-number">{{ severity_summary.critical }}</span>
                <span class="card-label">Critical</span>
            </div>
            <div class="card serious">
                <span class="card-number">{{ severity_summary.serious }}</span>
                <span class="card-label">Serious</span>
            </div>
            <div class="card moderate">
                <span class="card-number">{{ severity_summary.moderate }}</span>
                <span class="card-label">Moderate</span>
            </div>
            <div class="card minor">
                <span class="card-number">{{ severity_summary.minor }}</span>
                <span class="card-label">Minor</span>
            </div>
        </div>
        
        {% if quick_issues and quick_issues|length > 0 %}
        <section>
            <h2>Quick Issues Detected</h2>
            {% for issue in quick_issues[:20] %}
            <div class="issue">
                <div class="issue-header">
                    <span class="issue-title">{{ issue.type | replace('_', ' ') | title }}</span>
                    <span class="severity-badge severity-{{ issue.severity }}">{{ issue.severity }}</span>
                </div>
                <p>{{ issue.message }}</p>
                <div class="issue-details">
                    <div class="detail-item">
                        <span class="detail-label">Element</span>
                        <span class="detail-value">{{ issue.element }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">WCAG Criterion</span>
                        <span class="detail-value">{{ issue.wcag }}</span>
                    </div>
                    {% if issue.src %}
                    <div class="detail-item">
                        <span class="detail-label">Source</span>
                        <span class="detail-value">{{ issue.src }}</span>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </section>
        {% endif %}
        
        {% if wcag_violations and wcag_violations|length > 0 %}
        <section>
            <h2>WCAG Violations</h2>
            {% for violation in wcag_violations[:30] %}
            <div class="issue">
                <div class="issue-header">
                    <span class="issue-title">{{ violation.title or 'WCAG Violation' }}</span>
                    <span class="severity-badge severity-{{ violation.severity }}">{{ violation.severity }}</span>
                </div>
                <p>{{ violation.description or violation.message }}</p>
                <div class="issue-details">
                    <div class="detail-item">
                        <span class="detail-label">WCAG Level</span>
                        <span class="detail-value">{{ violation.level or 'AA' }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Criterion</span>
                        <span class="detail-value">{{ violation.criterion or 'N/A' }}</span>
                    </div>
                </div>
                
                {% if violation.recommendation %}
                <div class="recommendation">
                    <div class="recommendation-title">💡 Recommendation</div>
                    <p>{{ violation.recommendation }}</p>
                    {% if violation.code_example %}
                    <div class="code-block">{{ violation.code_example }}</div>
                    {% endif %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </section>
        {% endif %}
        
        {% if recommendations and recommendations|length > 0 %}
        <section>
            <h2>Prioritized Recommendations</h2>
            <table>
                <thead>
                    <tr>
                        <th>Priority</th>
                        <th>Issue</th>
                        <th>Effort</th>
                        <th>Impact</th>
                    </tr>
                </thead>
                <tbody>
                    {% for rec in recommendations[:15] %}
                    <tr>
                        <td>{{ rec.priority or 'Medium' }}</td>
                        <td>{{ rec.issue or 'General improvement' }}</td>
                        <td>{{ rec.effort or 'Medium' }}</td>
                        <td>{{ rec.impact or 'High' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>
        {% endif %}
        
        {% if aria_info %}
        <section>
            <h2>ARIA & Landmarks Analysis</h2>
            <div class="meta-info">
                <div class="meta-item">
                    <span class="meta-label">Total Images</span>
                    <span class="meta-value">{{ aria_info.totalImages }}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Images Without Alt</span>
                    <span class="meta-value">{{ aria_info.imagesWithoutAlt }}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Total Links</span>
                    <span class="meta-value">{{ aria_info.totalLinks }}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Empty Links</span>
                    <span class="meta-value">{{ aria_info.linksWithoutText }}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Landmarks Found</span>
                    <span class="meta-value">{{ aria_info.landmarksCount }}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Inputs Without Labels</span>
                    <span class="meta-value">{{ aria_info.inputsWithoutLabels }}</span>
                </div>
            </div>
        </section>
        {% endif %}
        
        {% if screenshot %}
        <section>
            <h2>Page Screenshot</h2>
            <img src="data:image/png;base64,{{ screenshot }}" alt="Page screenshot" class="screenshot">
        </section>
        {% endif %}
        
        <footer>
            <p>Generated by Accessibility Multi-Agent Platform</p>
            <p>Report ID: {{ report_id }} | Generated: {{ generated_at }}</p>
            <p>This report is based on automated testing and should be complemented with manual testing.</p>
        </footer>
    </div>
</body>
</html>
        ''')
        
        html_content = template.render(
            metadata=audit_data.get('metadata', {}),
            scanned_at=audit_data.get('scanned_at', datetime.utcnow().isoformat()),
            severity_summary=audit_data.get('severity_summary', {'critical': 0, 'serious': 0, 'moderate': 0, 'minor': 0}),
            quick_issues=audit_data.get('quick_issues', []),
            wcag_violations=audit_data.get('wcag_violations', []),
            recommendations=audit_data.get('recommendations', []),
            aria_info=audit_data.get('aria_info', {}),
            screenshot=audit_data.get('screenshot'),
            status_code=audit_data.get('status_code'),
            report_id=audit_data.get('report_id', 'unknown'),
            generated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        # Save HTML file
        filename = f"report_{audit_data.get('report_id', datetime.utcnow().timestamp())}.html"
        filepath = self.output_dir / filename
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(html_content)
        
        return str(filepath)
    
    def generate_pdf_report(self, audit_data: Dict[str, Any]) -> str:
        """Generate a PDF report from audit data."""
        
        report_id = audit_data.get('report_id', datetime.utcnow().timestamp())
        filename = f"report_{report_id}.pdf"
        filepath = self.output_dir / filename
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Title
        title = Paragraph("♿ Accessibility Audit Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Subtitle
        page_title = audit_data.get('metadata', {}).get('title', 'Unknown Page')
        subtitle = Paragraph(f"{page_title}", self.styles['Normal'])
        story.append(subtitle)
        story.append(Spacer(1, 0.5*inch))
        
        # Meta information
        meta_data = [
            ['URL:', audit_data.get('metadata', {}).get('url', 'N/A')],
            ['Audit Date:', audit_data.get('scanned_at', 'N/A')],
            ['Language:', audit_data.get('metadata', {}).get('lang', 'Not specified')],
            ['Status Code:', str(audit_data.get('status_code', 'N/A'))]
        ]
        
        meta_table = Table(meta_data, colWidths=[3*cm, 10*cm])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        severity_summary = audit_data.get('severity_summary', {})
        summary_data = [
            ['Severity', 'Count'],
            ['🔴 Critical', str(severity_summary.get('critical', 0))],
            ['🟠 Serious', str(severity_summary.get('serious', 0))],
            ['🟡 Moderate', str(severity_summary.get('moderate', 0))],
            ['🟢 Minor', str(severity_summary.get('minor', 0))]
        ]
        
        summary_table = Table(summary_data, colWidths=[10*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Quick Issues
        quick_issues = audit_data.get('quick_issues', [])
        if quick_issues:
            story.append(Paragraph("Quick Issues Detected", self.styles['SectionHeader']))
            
            for i, issue in enumerate(quick_issues[:20]):
                severity_colors = {
                    'critical': colors.red,
                    'serious': colors.orange,
                    'moderate': colors.gold,
                    'minor': colors.green
                }
                
                issue_title = issue.get('type', 'Unknown').replace('_', ' ').title()
                severity = issue.get('severity', 'moderate')
                
                story.append(Paragraph(
                    f"<b>{i+1}. {issue_title}</b> <font color='{severity_colors.get(severity, colors.black).hex()}'>[{severity.upper()}]</font>",
                    self.styles['SubsectionHeader']
                ))
                
                story.append(Paragraph(issue.get('message', ''), self.styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
                
                issue_details = f"<b>Element:</b> {issue.get('element', 'N/A')} | <b>WCAG:</b> {issue.get('wcag', 'N/A')}"
                story.append(Paragraph(issue_details, self.styles['Normal']))
                story.append(Spacer(1, 0.3*inch))
        
        # WCAG Violations
        wcag_violations = audit_data.get('wcag_violations', [])
        if wcag_violations:
            story.append(PageBreak())
            story.append(Paragraph("WCAG Violations", self.styles['SectionHeader']))
            
            for i, violation in enumerate(wcag_violations[:20]):
                story.append(Paragraph(
                    f"<b>{i+1}. {violation.get('title', 'WCAG Violation')}</b>",
                    self.styles['SubsectionHeader']
                ))
                
                description = violation.get('description', violation.get('message', ''))
                story.append(Paragraph(description, self.styles['Normal']))
                
                if violation.get('recommendation'):
                    story.append(Spacer(1, 0.2*inch))
                    story.append(Paragraph(
                        f"<b>💡 Recommendation:</b> {violation.get('recommendation')}",
                        self.styles['Normal']
                    ))
                
                story.append(Spacer(1, 0.3*inch))
        
        # Recommendations
        recommendations = audit_data.get('recommendations', [])
        if recommendations:
            story.append(PageBreak())
            story.append(Paragraph("Prioritized Recommendations", self.styles['SectionHeader']))
            
            rec_data = [['Priority', 'Issue', 'Effort', 'Impact']]
            for rec in recommendations[:15]:
                rec_data.append([
                    rec.get('priority', 'Medium'),
                    rec.get('issue', 'General improvement'),
                    rec.get('effort', 'Medium'),
                    rec.get('impact', 'High')
                ])
            
            rec_table = Table(rec_data, colWidths=[3*cm, 7*cm, 3*cm, 3*cm])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(rec_table)
        
        # Footer
        story.append(PageBreak())
        story.append(Spacer(1, 1*inch))
        footer_text = f"""
        <para alignment="center">
            <b>Generated by Accessibility Multi-Agent Platform</b><br/>
            Report ID: {report_id} | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>
            <i>This report is based on automated testing and should be complemented with manual testing.</i>
        </para>
        """
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return str(filepath)
    
    async def generate_json_report(self, audit_data: Dict[str, Any]) -> str:
        """Generate a JSON report from audit data."""
        import json
        
        report_id = audit_data.get('report_id', datetime.utcnow().timestamp())
        filename = f"report_{report_id}.json"
        filepath = self.output_dir / filename
        
        json_report = {
            'report_id': report_id,
            'generated_at': datetime.utcnow().isoformat(),
            'metadata': audit_data.get('metadata', {}),
            'scanned_at': audit_data.get('scanned_at'),
            'status_code': audit_data.get('status_code'),
            'severity_summary': audit_data.get('severity_summary', {}),
            'quick_issues': audit_data.get('quick_issues', []),
            'wcag_violations': audit_data.get('wcag_violations', []),
            'recommendations': audit_data.get('recommendations', []),
            'aria_info': audit_data.get('aria_info', {}),
            'has_screenshot': bool(audit_data.get('screenshot'))
        }
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(json_report, indent=2, default=str))
        
        return str(filepath)
    
    async def generate_all_formats(self, audit_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate reports in all formats (HTML, PDF, JSON)."""
        
        html_path = await self.generate_html_report(audit_data)
        pdf_path = self.generate_pdf_report(audit_data)
        json_path = await self.generate_json_report(audit_data)
        
        return {
            'html': html_path,
            'pdf': pdf_path,
            'json': json_path
        }
