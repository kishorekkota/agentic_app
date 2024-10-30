# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from azure_rag import query_azure_search, generate_response
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

@app.post("/query", response_model=QueryResponse)
async def query_azure(query_request: QueryRequest):
    query = query_request.query
    logger.info(f"Received query: {query}")
    try:
        sources = query_azure_search(query)
        if not sources:
            logger.warning("No sources found for the query.")
            raise HTTPException(status_code=404, detail="No sources found for the query.")
        response = generate_response(query, sources)
        logger.info("Query processed successfully")
        return QueryResponse(response=response)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))