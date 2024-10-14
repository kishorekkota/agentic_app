from fastapi import FastAPI, Request
from pydantic import BaseModel

from ai_bot_openai import AIAssistant

app = FastAPI()

assistant = AIAssistant()


# Pydantic model to define the structure of incoming requests
class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message

    print("user_message: ", user_message)

    assistant.new_conversation = True
  
    bot_response = assistant.run(user_message)

    return {"response": bot_response}