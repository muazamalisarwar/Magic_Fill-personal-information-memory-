# Personal Information Memory & Intelligent Form Completion — Backend API

A high-performance, modular, and scalable RESTful backend API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL** (with zero-configuration SQLite compatibility for local testing).

This service acts as the core memory layer for user identity, detailed personal and academic profiles, and multi-role professional experiences. Designed as the backend foundation for an intelligent form auto-completion system with future AI/vector embedding extensibility.

---

## 📌 Project Overview

- **Project:** Personal Information Memory & Intelligent Form Completion
- **Subsystem:** Backend REST API
- **Framework:** FastAPI + Pydantic v2 + SQLAlchemy 2.0
- **Primary Database:** PostgreSQL (`psycopg2-binary`)
- **Local Fallback Database:** SQLite

---

## 🏗️ Architecture & Project Structure

The project follows a clean, decoupled layered architecture:

```
Request ──> Router ──> Pydantic Validation ──> Service Layer ──> SQLAlchemy ORM ──> PostgreSQL / SQLite ──> Response Schema ──> Client
```

### Directory Layout

```text
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application factory, middleware, exception handlers
│   ├── exceptions.py               # Custom domain exceptions
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py             # Engine, declarative base, sessionmaker, and get_db dependency
│   │   └── models.py               # SQLAlchemy ORM models (User, PersonalInfo, Experience)
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py               # APIResponse[T], ErrorResponse, HealthResponse
│   │   ├── user.py                 # UserCreate, UserResponse
│   │   ├── personal_info.py        # PersonalInfoCreate, PersonalInfoUpdate, PersonalInfoResponse
│   │   └── experience.py           # ExperienceCreate, ExperienceUpdate, ExperienceResponse
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py                # User management endpoints (/api/users)
│   │   ├── personal_info.py        # Personal info endpoints (/api/users/{user_id}/personal-info)
│   │   └── experiences.py          # Experience endpoints (/api/users/{user_id}/experiences, /api/experiences/{id})
│   │
│   └── services/
│       ├── __init__.py
│       ├── user_service.py         # Business and persistence logic for users
│       ├── personal_info_service.py# Business and persistence logic for personal profiles
│       └── experience_service.py   # Business and persistence logic for experiences
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Isolated in-memory SQLite fixture and TestClient setup
│   ├── test_health.py              # Health check, docs, and schema tests
│   ├── test_personal_info.py       # User and Personal Info CRUD & validation tests
│   └── test_experiences.py        # Multi-experience CRUD and date validation tests
│
├── .env.example                    # Template environment variables
├── .env                            # Local environment configuration (git-ignored)
├── .gitignore                      # Git ignore rules for venv, env files, and sqlite dbs
├── pytest.ini                      # Pytest discovery and pythonpath configuration
├── requirements.txt                # Production and development dependencies
└── README.md                       # Documentation and usage guide
```

---

## 🗄️ Relational Database Schema

### Entity Relationship Model

```
┌──────────────────┐           1 : 1           ┌────────────────────────────┐
│      users       │ ───────────────────────── │       personal_info        │
├──────────────────┤                           ├────────────────────────────┤
│ id (PK, int)     │                           │ id (PK, int)               │
│ created_at (ts)  │                           │ user_id (FK -> users.id, U)│
│ updated_at (ts)  │                           │ full_name (str)            │
└────────┬─────────┘                           │ father_name (str)          │
         │                                     │ date_of_birth (date)       │
         │ 1 : N                               │ cnic (str)                 │
         │                                     │ phone (str)                │
         ▼                                     │ email (str)                │
┌────────────────────────────┐                 │ address, city, country...  │
│        experiences         │                 │ university, degree, etc.   │
├────────────────────────────┤                 │ created_at, updated_at     │
│ id (PK, int)               │                 └────────────────────────────┘
│ user_id (FK -> users.id)   │
│ company (str)              │
│ job_title (str)            │
│ start_date (date)          │
│ end_date (date, nullable)  │  <-- Null indicates currently active role
│ description (text)         │
│ skills (text)              │
│ created_at, updated_at     │
└────────────────────────────┘
```

---

## ⚙️ Requirements

- **Python:** 3.11+ / 3.12+ (tested through 3.14)
- **pip:** Package installer for Python
- **PostgreSQL:** Primary production database (version 14+)

---

## 🚀 Installation & Setup

### 1. Clone the repository & Navigate to backend

```bash
cd backend
```

### 2. Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux / macOS:**
```bash
cp .env.example .env
```

Open `.env` and set your credentials:

```ini
# PostgreSQL (Primary production database):
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/personal_memory_db

# Or use SQLite for instant zero-config local testing:
# DATABASE_URL=sqlite:///./personal_memory.db

APP_NAME=Personal Information Memory API
APP_ENV=development
DEBUG=True
API_V1_PREFIX=/api
HOST=127.0.0.1
PORT=8000
```

### 5. Create PostgreSQL Database (When using PostgreSQL)

In `psql` or `pgAdmin`:

```sql
CREATE DATABASE personal_memory_db;
```

---

## 🏃 Running the Application

From the `backend/` directory, run:

```bash
uvicorn app.main:app --reload
```

The application will start at:
- **Server:** `http://127.0.0.1:8000`
- **Health Check:** `http://127.0.0.1:8000/health`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Interactive ReDoc Documentation:** `http://127.0.0.1:8000/redoc`
- **OpenAPI Schema (JSON):** `http://127.0.0.1:8000/openapi.json`

---

## 📡 API Reference

### Response Formats

#### Success Envelope (`200 OK` / `201 Created`):
```json
{
  "success": true,
  "message": "Personal information retrieved successfully",
  "data": { ... }
}
```

#### Error Envelope (`400`, `404`, `422`, `500`):
```json
{
  "success": false,
  "message": "User with ID 1 was not found",
  "error_code": "USER_NOT_FOUND"
}
```

### Endpoints Table

| Category | Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- | :--- |
| **System** | `GET` | `/health` | Check service health | `200` |
| **Users** | `POST` | `/api/users` | Register a new user identity | `201` |
| **Users** | `GET` | `/api/users/{user_id}` | Retrieve a user profile by ID | `200` / `404` |
| **Personal Info** | `POST` | `/api/users/{user_id}/personal-info` | Create 1-to-1 personal profile | `201` / `400` / `404` |
| **Personal Info** | `GET` | `/api/users/{user_id}/personal-info` | Retrieve user's personal profile | `200` / `404` |
| **Personal Info** | `PUT` | `/api/users/{user_id}/personal-info` | Update personal profile (partial) | `200` / `404` |
| **Experiences** | `POST` | `/api/users/{user_id}/experiences` | Add a new work experience | `201` / `404` / `422` |
| **Experiences** | `GET` | `/api/users/{user_id}/experiences` | List all experiences for a user | `200` / `404` |
| **Experiences** | `GET` | `/api/experiences/{experience_id}` | Get single experience by ID | `200` / `404` |
| **Experiences** | `PUT` | `/api/experiences/{experience_id}` | Update experience by ID | `200` / `404` / `422` |

---

## 🧪 Testing

The test suite runs using **Pytest** with an in-memory SQLite database (`sqlite:///:memory:`). No running PostgreSQL database or manual migrations are required to run tests.

Execute from the `backend/` directory:

```bash
pytest
```

For verbose output with test names:

```bash
pytest -v
```

---

## 🔮 Future Extensibility (AI & Vector Database Integration)

This backend is architected to cleanly support future phases of the project:

```
Browser Extension / Web Client
           │
           ▼
     FastAPI Backend
     ┌──────────────────────┬──────────────────────┐
     │                      │                      │
     ▼                      ▼                      ▼
Relational DB         AI Service Layer       Vector Database
(PostgreSQL / SQLite)  ├── Embeddings         (FAISS / pgvector)
                      ├── Semantic Matcher
                      └── Relevance Ranker
```

- **Clean Decoupling:** Database models and business services contain no hardcoded vector schemas or embedding logic.
- **Service-Oriented:** New AI services (such as semantic field mapping, sentence transformers, and FAISS indexing) can be added as standalone modules in `app/services/ai/` and integrated into routers without altering existing relational contracts.
