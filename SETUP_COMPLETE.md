# Accessibility Multi-Agent Platform - Setup Guide

## ✅ Changes Completed

### 1. PostgreSQL Persistence Implementation
- **Created SQLAlchemy models** in `/workspace/backend/app/models/`:
  - `user.py` - User authentication table
  - `audit.py` - Audit results storage
  - `monitor.py` - Continuous monitoring configurations
  - `wcag_rule.py` - WCAG standards reference with vector embeddings

- **Database connection** configured in `/workspace/backend/app/db/database.py`
- **Updated API endpoints** to use database instead of in-memory storage:
  - All audit endpoints now persist to PostgreSQL
  - Cache layer for active audits (fast access during processing)
  - Fallback to database for completed/past audits

### 2. Database Initialization Script
- **Created** `/workspace/scripts/init-db.sh`:
  - Waits for PostgreSQL to be ready
  - Runs schema initialization from `init.sql`
  - Creates storage directories for reports and screenshots
  - Automatically executed on backend startup

### 3. Updated Docker Compose
- Backend service now runs initialization script before starting
- Storage directories mounted for persistent file storage
- Database schema automatically applied on first run

### 4. Application Lifespan Management
- **Updated** `/workspace/backend/app/main.py`:
  - Database tables initialized on application startup
  - Graceful error handling if DB is not ready

## 🚀 How to Run

```bash
# From the /workspace directory
docker-compose up --build
```

This will:
1. Start PostgreSQL with pgvector extension
2. Initialize database schema automatically
3. Create all required tables (users, audits, monitors, wcag_rules)
4. Start backend API with database persistence
5. Start frontend dashboard
6. Start Redis, Ollama, and other services

## 📊 What Changed in the API

### Before (In-Memory):
- Audits lost on restart
- No historical data
- No multi-user support

### After (PostgreSQL):
- ✅ Persistent audit history
- ✅ Trend analysis over time
- ✅ Multi-user architecture ready
- ✅ Monitor configurations saved
- ✅ WCAG rules reference table with vector search

## 🔍 Testing the Setup

Once running:

1. **Check Swagger docs**: http://localhost:8000/docs
2. **Start an audit**: POST to `/api/v1/accessibility/audit`
3. **Check status**: GET `/api/v1/accessibility/audit/{id}`
4. **View in database**: 
   ```bash
   docker exec -it accessibility-db psql -U postgres -d accessibility_db
   \dt  # List tables
   SELECT * FROM audits;  # View audits
   ```

## 📁 New File Structure

```
backend/
├── app/
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py          # NEW: DB connection & session management
│   ├── models/
│   │   ├── __init__.py          # UPDATED: Model exports
│   │   ├── user.py              # NEW: User model
│   │   ├── audit.py             # NEW: Audit model
│   │   ├── monitor.py           # NEW: Monitor model
│   │   └── wcag_rule.py         # NEW: WCAG rule model
│   ├── api/v1/
│   │   └── audit.py             # UPDATED: Uses DB instead of memory
│   └── main.py                  # UPDATED: DB initialization on startup
└── db/
    └── init.sql                 # Existing: Schema definition

scripts/
└── init-db.sh                   # NEW: Auto-initialization script
```

## 🎯 Next Steps

The platform now has:
- ✅ Persistent storage with PostgreSQL
- ✅ Automatic database initialization
- ✅ Proper ORM models with SQLAlchemy

Ready to test end-to-end functionality!
