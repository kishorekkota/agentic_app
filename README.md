# agentic_app

Monorepo for multiple LLM/RAG experiments and API/UI implementations.

## Active Components

- `app/`: Main FastAPI + LangGraph backend.
- `ui/` and `updated_ui/`: Streamlit/UI clients.
- `updated_api/`: Alternate API implementation.

Other folders are prototypes, backups, or experimental tracks.

## Quick Start (app)

```bash
cd app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Required environment variables for core runtime:

- `OPENAI_API_KEY`
- `TAVILY_API_KEY`
- `OPENCAGE_API_KEY`
- `MONGODB_URI`

Optional for persistence and Azure retrieval:

- `DBHOST`, `DBNAME`, `DBUSER`, `DBPASSWORD`, `SSLMODE`
- `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_KEY`, `SEARCH_INDEX_NAME`
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`

## Refactor Branch Notes

Current cleanup/refactor work is on branch:

- `chore/full-app-refactor-cleanup-docs`

Detailed change log is documented in:

- `docs/refactor_cleanup.md`