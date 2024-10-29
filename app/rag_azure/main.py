# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph_agent import LangGraphAgent

app = FastAPI()
agent = LangGraphAgent()

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def query(request: QueryRequest):
    try:
        answer = agent.get_answer(request.query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)