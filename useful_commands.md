### Running Fast API
uvicorn fast_api:app --reload  


### Running Streamlit UI
streamlit run app_ui.py       


### Env Variable for Running Model
export OPENAI_API_KEY=${OPENAI_API_KEY}
export LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
export OPENCAGE_API_KEY=${OPENCAGE_API_KEY}
export TAVILY_API_KEY=${TAVILY_API_KEY}


### API Endpoint


### Docker Run Command
docker run -p 80:80  \     -e OPENAI_API_KEY=<> \
     -e LANGCHAIN_API_KEY=<> \
     -e LANGCHAIN_OPENAI_API_KEY=<> \
     -e OPENCAGE_API_KEY=<>  \
     -e TAVILY_API_KEY=<> \
     -e DB_URI=<> \
        kishorekkota/ai_bot:v1



https://github.com/Azure-Samples/azure-search-python-samples/blob/main/Tutorial-RAG/Tutorial-rag.ipynb


https://github.com/etienne113/Chatbot/blob/48baa52f1eca85d1c09e8367bb7cc514409c5998/backend/tools/tools.py