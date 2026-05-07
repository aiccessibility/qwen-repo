# Accessibility Multi-Agent Platform - Developer Guide

## Overview

This is a multi-agent AI platform for automated web accessibility auditing, continuous monitoring, and developer APIs. Built with LangGraph, FastAPI, Next.js, and open-source LLMs.

## Architecture

### Multi-Agent System

The platform uses LangGraph to orchestrate specialized AI agents:

1. **Auditor Agent** - Scans web pages and analyzes WCAG compliance
2. **Monitor Agent** - Tracks accessibility changes over time
3. **Reporter Agent** - Generates comprehensive reports

### Tech Stack

- **Backend**: Python 3.11+, FastAPI, LangGraph, Playwright
- **Frontend**: Next.js 14, React, Tailwind CSS
- **Database**: PostgreSQL 16 with pgvector
- **Cache/Queue**: Redis 7
- **LLMs**: Open-source models via Ollama (Llama 2, Mistral, etc.)
- **Task Queue**: Celery for async processing

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd accessibility-platform
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start all services**
```bash
docker-compose up --build
```

4. **Access the services**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Dashboard: http://localhost:3000
- Ollama: http://localhost:11434

### First Steps

1. **Pull LLM models** (first time only)
```bash
docker exec accessibility-ollama ollama pull llama2:13b
docker exec accessibility-ollama ollama pull llama2:70b
```

2. **Test the API**
```bash
curl -X POST http://localhost:8000/api/v1/accessibility/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "wcag_level": "AA"}'
```

3. **Open the dashboard**
Navigate to http://localhost:3000 and enter a URL to audit.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph agents and workflows
│   │   │   └── workflow.py  # Agent definitions and graph creation
│   │   ├── api/             # FastAPI routes
│   │   │   └── v1/
│   │   │       ├── audit.py # Audit endpoints
│   │   │       └── router.py
│   │   ├── db/              # Database initialization
│   │   ├── models/          # Pydantic and SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   └── utils/           # Config, helpers
│   ├── tests/               # Test suite
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js app router
│   │   ├── components/      # React components
│   │   └── styles/          # Tailwind CSS
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml       # Full stack orchestration
├── .env.example            # Environment template
└── README.md
```

## API Endpoints

### Auditing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/accessibility/audit` | Start new audit |
| GET | `/api/v1/accessibility/audit/{id}` | Get audit status |
| GET | `/api/v1/accessibility/audit/{id}/report` | Download report |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/accessibility/monitor` | Start monitoring |
| DELETE | `/api/v1/accessibility/monitor/{id}` | Stop monitoring |

### WCAG Standards

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/accessibility/wcag/rules` | Get WCAG rules |

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Configuration

### LLM Models

Edit `.env` to change LLM models:

```bash
LLM_MODEL_AUDITOR=llama2:70b    # For complex analysis
LLM_MODEL_MONITOR=llama2:13b    # For routine checks
LLM_MODEL_REPORTER=llama2:70b   # For report generation
```

Supported providers:
- `ollama` (default, local)
- `vllm` (local, faster)
- Any OpenAI-compatible API

### Database

The platform uses PostgreSQL with pgvector for:
- Storing audit results
- Vector embeddings of WCAG rules
- Historical trend analysis

### Celery Tasks

Async tasks are handled by Celery:
- Long-running audits
- Scheduled monitoring
- Report generation

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Set `DEBUG=false`
- [ ] Configure CORS properly
- [ ] Use production database credentials
- [ ] Enable HTTPS
- [ ] Set up proper logging
- [ ] Configure backup strategy

### Scaling Considerations

- Use multiple Celery workers for high load
- Consider GPU acceleration for Ollama
- Implement rate limiting on API
- Add caching layer for frequently accessed data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: Report bugs and feature requests
- Documentation: Check `/docs` folder
- API Docs: http://localhost:8000/docs

## Roadmap

- [ ] PDF accessibility auditing
- [ ] Automated remediation suggestions
- [ ] Browser extension
- [ ] CI/CD integrations
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] SCORM compliance training modules
