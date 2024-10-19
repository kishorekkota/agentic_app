from fastapi import FastAPI, Request
from pydantic import BaseModel

from ai_assistant import AIAssistant

app = FastAPI()



# Pydantic model to define the structure of incoming requests
class ChatRequest(BaseModel):
    message: str
    new_chat: bool = False
    thread_id: str 


@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message

    print("user_message: ", user_message + " new_chat: ", request.new_chat)
    print(" thread_id: ", request.thread_id)

    assistant = AIAssistant(request.thread_id, request.new_chat)

    if(request.new_chat):
        assistant.new_conversation = True
    else:
        assistant.thread_id = request.thread_id
  
    bot_response = assistant.run(user_message)

    return {bot_response}