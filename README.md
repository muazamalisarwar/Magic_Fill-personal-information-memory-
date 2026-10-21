# Magic Fill — Personal Information Memory & Intelligent Form Completion

Team university project for intelligent form auto-completion using personal information memory.

## Project Structure

- `backend/`: FastAPI backend REST API with PostgreSQL database, Pydantic schemas, Groq LLM integration, and Pytest suite.
- `extension/`: Chromium browser extension (Manifest V3) for intelligent DOM form inspection and automated completion.

## Getting Started with the Backend

Please refer to the detailed [Backend Documentation](file:///backend/README.md) inside the `backend/` folder:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
