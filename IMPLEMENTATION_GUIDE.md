# Implementation Guide: Playwright + LangGraph + Ollama + Report Generation

This document describes the implementation of the three key features you requested:

## ✅ 1. Playwright Integration

**File**: `/workspace/backend/app/services/playwright_scanner.py`

### Features Implemented:

- **Full page scanning** with headless Chromium
- **HTML extraction** for LLM analysis
- **Screenshot capture** (full page, base64 encoded)
- **Accessibility tree extraction** (ARIA roles, labels, landmarks)
- **Quick issue detection** (missing alt, empty links, unlabeled inputs, etc.)
- **Metadata extraction** (language, landmarks, heading structure)

### Key Methods:

```python
scanner = PlaywrightScanner(headless=True)
await scanner.start()

# Scan a page
result = await scanner.scan_page("https://example.com")

# Result contains:
# - html_content: Full HTML
# - screenshot: Base64 PNG
# - aria_tree: Accessibility tree structure
# - aria_info: ARIA statistics
# - quick_issues: Auto-detected issues
# - metadata: Page metadata
```

### Quick Issues Detected Automatically:

- Missing `lang` attribute on `<html>`
- Missing or multiple `<h1>` tags
- Images without `alt` attribute
- Empty links (no text or aria-label)
- Form inputs without labels
- Missing landmark regions

---

## ✅ 2. LangGraph + Ollama Integration

**File**: `/workspace/backend/app/agents/workflow.py`

### Architecture:

```
┌─────────────────────────────────────────────┐
│         LangGraph Workflow                  │
│                                             │
│  ┌──────────────┐                          │
│  │ AuditorAgent │──┐                        │
│  │ (llama2:70b) │  │                        │
│  └──────────────┘  │                        │
│        │           │                        │
│        ▼           │                        │
│  ┌──────────────┐  │                        │
│  │ MonitorAgent │  │                        │
│  │ (llama2:13b) │  │                        │
│  └──────────────┘  │                        │
│        │           │                        │
│        ▼           ▼                        │
│  ┌──────────────┐                          │
│  │ReporterAgent │                          │
│  │ (llama2:70b) │                          │
│  └──────────────┘                          │
└─────────────────────────────────────────────┘
              │
              ▼
      ┌───────────────┐
      │    Ollama     │
      │  (localhost)  │
      │ :11434        │
      └───────────────┘
```

### Agent Workflows:

#### Audit Workflow:
1. **scan_page** → Playwright scans the URL
2. **analyze_violations** → LLM analyzes HTML + ARIA data
3. **generate_recommendations** → Prioritized fix suggestions
4. **generate_report** → PDF/HTML/JSON reports

#### Monitor Workflow:
1. **check_changes** → Re-scan and compare with previous
2. **alert_if_needed** → Detect regressions
3. **generate_report** → Updated report

### LLM Configuration:

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama2:70b",  # or "llama2:13b" for lighter tasks
    base_url="http://ollama:11434",
    temperature=0.1,
    format="json"  # Force JSON output
)
```

### Prompt Template:

The system uses a structured prompt that includes:
- System role: Expert WCAG auditor
- Input data: Metadata, ARIA info, quick issues, HTML snippet, accessibility tree
- Output format: Structured JSON with violations and severity summary

---

## ✅ 3. Real PDF/HTML Report Generation

**File**: `/workspace/backend/app/services/report_generator.py`

### Supported Formats:

- **HTML** → Interactive, responsive web report
- **PDF** → Professional, printable document
- **JSON** → Machine-readable data

### HTML Report Features:

- Modern, responsive design with Tailwind-like CSS
- Executive summary with severity cards
- Detailed issue list with WCAG criteria
- Recommendations table
- ARIA & landmarks analysis
- Embedded screenshot
- Print-friendly styles

### PDF Report Features:

- Professional layout using ReportLab
- Custom styles and branding colors
- Tables for summary and recommendations
- Page breaks between sections
- Footer with metadata

### Usage:

```python
generator = ReportGenerator(output_dir="/app/reports")

# Generate all formats
report_paths = await generator.generate_all_formats(audit_data)

# Returns:
# {
#   'html': '/app/reports/report_xxx.html',
#   'pdf': '/app/reports/report_xxx.pdf',
#   'json': '/app/reports/report_xxx.json'
# }
```

---

## 📡 API Endpoints

**File**: `/workspace/backend/app/api/v1/audit.py`

### New Endpoints:

#### 1. Start Audit
```bash
POST /api/v1/audit
{
  "url": "https://example.com",
  "wcag_level": "AA",
  "include_screenshots": true
}

Response:
{
  "audit_id": "uuid-here",
  "status": "pending",
  "message": "Audit started successfully"
}
```

#### 2. Check Status
```bash
GET /api/v1/audit/{audit_id}

Response:
{
  "audit_id": "uuid-here",
  "status": "completed",  # pending, processing, completed, error
  "progress": 100,
  "violations_count": 15,
  "severity_summary": {
    "critical": 2,
    "serious": 5,
    "moderate": 6,
    "minor": 2
  }
}
```

#### 3. Download Report
```bash
# PDF
GET /api/v1/audit/{audit_id}/report?format=pdf

# HTML
GET /api/v1/audit/{audit_id}/report?format=html

# JSON
GET /api/v1/audit/{audit_id}/report?format=json
```

#### 4. Get Full Results
```bash
GET /api/v1/audit/{audit_id}/results

Response:
{
  "audit_id": "uuid-here",
  "url": "https://example.com",
  "metadata": {...},
  "severity_summary": {...},
  "wcag_violations": [...],
  "quick_issues": [...],
  "recommendations": [...],
  "aria_info": {...},
  "report_paths": {
    "html": "...",
    "pdf": "...",
    "json": "..."
  }
}
```

#### 5. Start Monitoring
```bash
POST /api/v1/monitor
{
  "url": "https://example.com"
}
```

---

## 🚀 How to Run

### 1. Start the Stack

```bash
cd /workspace
docker-compose up --build
```

### 2. Pull LLM Models (first time only)

```bash
# Wait for Ollama to start
docker exec accessibility-ollama ollama pull llama2:13b
docker exec accessibility-ollama ollama pull llama2:70b  # Optional, for better results
```

### 3. Install Playwright Browsers

```bash
docker exec accessibility-backend playwright install chromium
docker exec accessibility-backend playwright install-deps chromium
```

### 4. Access Services

- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3000
- **Reports**: http://localhost:8000/reports/

---

## 🧪 Test the Full Flow

### Using curl:

```bash
# 1. Start an audit
AUDIT_ID=$(curl -s -X POST http://localhost:8000/api/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' \
  | jq -r '.audit_id')

echo "Audit ID: $AUDIT_ID"

# 2. Wait and check status
sleep 30
curl http://localhost:8000/api/v1/audit/$AUDIT_ID | jq

# 3. Download PDF report
curl -o report.pdf http://localhost:8000/api/v1/audit/$AUDIT_ID/report?format=pdf

# 4. Download HTML report
curl -o report.html http://localhost:8000/api/v1/audit/$AUDIT_ID/report?format=html
```

### Using the Swagger UI:

1. Go to http://localhost:8000/docs
2. Click on `POST /api/v1/audit`
3. Enter a URL (e.g., `https://example.com`)
4. Click "Execute"
5. Copy the `audit_id` from the response
6. Use `GET /api/v1/audit/{audit_id}` to check status
7. Once completed, use `GET /api/v1/audit/{audit_id}/report?format=pdf` to download

---

## 📊 Example Output

### Violation Object:

```json
{
  "title": "Missing Alt Attribute",
  "description": "Image is missing alternative text",
  "severity": "critical",
  "level": "A",
  "criterion": "1.1.1",
  "element": "img.hero-image",
  "recommendation": "Add descriptive alt text that conveys the image's purpose",
  "code_example": "<img src='hero.jpg' alt='Team collaborating in modern office'>"
}
```

### Severity Summary:

```json
{
  "critical": 2,
  "serious": 5,
  "moderate": 6,
  "minor": 2
}
```

### Recommendation Object:

```json
{
  "priority": "P1",
  "issue": "Missing Alt Attribute",
  "effort": "Low",
  "impact": "High",
  "severity": "critical",
  "wcag_criterion": "1.1.1",
  "fix_description": "Add descriptive alt text..."
}
```

---

## 🔧 Configuration

### Environment Variables (.env):

```bash
# Ollama
OLLAMA_BASE_URL=http://ollama:11434
LLM_MODEL_AUDITOR=llama2:70b
LLM_MODEL_MONITOR=llama2:13b

# Playwright
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000

# Reports
REPORT_OUTPUT_DIR=/app/reports
ENABLE_SCREENSHOTS=true
```

---

## 🛠️ Troubleshooting

### Issue: Ollama connection refused

```bash
# Check if Ollama is running
docker ps | grep ollama

# Check logs
docker logs accessibility-ollama

# Restart Ollama
docker-compose restart ollama
```

### Issue: Playwright browser not found

```bash
# Install browsers
docker exec accessibility-backend playwright install chromium

# Install system dependencies
docker exec accessibility-backend playwright install-deps chromium
```

### Issue: LLM returns invalid JSON

The code includes fallback parsing that handles:
- Markdown code blocks (```json ... ```)
- Extra whitespace
- Partial responses

If parsing fails, it returns empty violations but doesn't crash.

---

## 📈 Next Steps

1. **Add Database Persistence** → Replace in-memory store with PostgreSQL
2. **Implement Queue System** → Use Celery + Redis for long-running audits
3. **Add Authentication** → JWT-based user authentication
4. **Enhance LLM Prompts** → Fine-tune for better violation detection
5. **Add More WCAG Rules** → Expand automated checks
6. **Implement Contrast Checking** → Color contrast analysis
7. **Add CI/CD Integration** → GitHub Actions, GitLab CI plugins

---

## 📝 Summary

You now have a fully functional MVP with:

✅ **Playwright Integration** - Real web page scanning  
✅ **LangGraph + Ollama** - Multi-agent AI workflow with open-source LLMs  
✅ **Report Generation** - Professional PDF, HTML, and JSON reports  
✅ **Complete API** - RESTful endpoints with Swagger documentation  
✅ **Background Processing** - Async workflow execution  

The platform is ready for testing and iteration!
