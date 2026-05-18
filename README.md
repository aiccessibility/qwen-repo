# Accessibility Multi-Agent Platform

A multi-agent AI platform for automated web accessibility auditing, continuous monitoring, and developer APIs.

## Features

- **Automated Accessibility Auditing**: WCAG 2.1/2.2 compliance scanning using AI agents
- **Continuous Monitoring**: Autonomous agents that track accessibility over time
- **Developer API**: RESTful API with Swagger documentation for integration
- **Multi-Agent Architecture**: Built with LangGraph for coordinated agent workflows
- **Open-Source LLMs**: Support for local and cloud open-source models

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, LangGraph
- **Frontend**: Next.js, React, Tailwind CSS
- **Database**: PostgreSQL with pgvector
- **Queue**: Redis + Celery
- **Containerization**: Docker & Docker Compose
- **LLMs**: Open-source models (Llama, Mistral, etc.) via Ollama/vLLM

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agents/       # LangGraph agents (Auditor, Monitor, Reporter)
│   │   ├── services/     # Business logic (scraping, analysis, reporting)
│   │   ├── api/          # FastAPI routes and Swagger docs
│   │   ├── models/       # Pydantic models and DB schemas
│   │   ├── db/           # Database connections and migrations
│   │   └── utils/        # Helpers, config, logging
│   └── tests/            # Unit and integration tests
├── frontend/             # Next.js dashboard
├── docs/                 # Documentation
├── docker-compose.yml    # Full stack orchestration
└── README.md
```

## Quick Start

```bash
# Start all services with Docker
docker-compose up --build

# Access services
# - API: http://localhost:8000
# - Swagger Docs: http://localhost:8000/docs
# - Dashboard: http://localhost:3000
```

## License

MIT
