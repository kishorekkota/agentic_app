from dataclasses import dataclass

@dataclass
class ChatBot:
    request: str
    response: str
    thread_id: str

    def get_response(self):
        return self.response
    
    def __str__(self) -> str:
        return f"ChatBot(response={self.response}, request={self.request}, thread_id={self.thread_id})"