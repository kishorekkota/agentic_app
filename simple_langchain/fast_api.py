from fastapi import FastAPI, Request
from pydantic import BaseModel

import langchain_with_function

app = FastAPI()



# Pydantic model to define the structure of incoming requests
class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message

    print("user_message: ", user_message)
  
    bot_response = langchain_with_function.call_model(user_message)  

    return {"response": bot_response}