# App Module

FastAPI backend for chat orchestration with LangGraph.

## Run Locally

```bash
cd app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Key Files

- `main.py`: FastAPI app bootstrap, lifespan management, validation handler.
- `routes.py`: API endpoints (`/chat`, `/chat/history`, `/chat/additional_info`, `/chat/feedback`).
- `ai_assistant.py`: LangGraph workflow and tool orchestration.
- `tools.py`: External tools (Tavily search, weather API, Azure RAG retrieval).
- `db_connection.py`: Postgres pool initialization for optional checkpointing.

## Notes

- JWT dependency is applied at router registration level.
- Postgres checkpointer is optional and auto-disabled when DB env vars are missing.
- History/additional-info/feedback routes return HTTP 501 if those assistant capabilities are not implemented in the active assistant class.

