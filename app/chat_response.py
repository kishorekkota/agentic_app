from dataclasses import dataclass
from enum import Enum

class InfoType(Enum):
    STATE = "state"
    ZIPCODE = "zipcode"

@dataclass
class ChatBot:
    request: str
    response: str
    thread_id: str
    run_id: str
    addtion_info_needed: bool = False
    info_type: InfoType = None

    def get_response(self):
        return self.response
    
    def __str__(self) -> str:
        return f"ChatBot(response={self.response}, request={self.request}, thread_id={self.thread_id}, run_id={self.run_id}, info_type={self.info_type})"