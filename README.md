# Magic Fill — Personal Information Memory & Intelligent Form Completion

Team university project for intelligent form auto-completion using personal information memory.

## Project Structure

- `backend/`: FastAPI backend REST API with PostgreSQL/SQLite database, Pydantic schemas, and Pytest suite.
- *(Future)* `extension/`: Chrome/browser extension for intelligent DOM inspection and form auto-completion.
- *(Future)* `ai-engine/`: Semantic matching, sentence embeddings, and vector database ranker.

## Getting Started with the Backend

Please refer to the detailed [Backend Documentation](file:///backend/README.md) inside the `backend/` folder:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
