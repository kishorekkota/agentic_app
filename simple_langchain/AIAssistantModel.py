from dataclasses import dataclass
from uuid import uuid4
import uuid

@dataclass
class AIAssistant:
    def __init__(self, user_message, system_message, thread_id, new_conversation=False):
        self.user_message = user_message
        self.system_message = system_message
        self.thread_id = thread_id
        self.new_conversation = new_conversation
        self.response = None
        self.clarify_questions = []
        self.need_clarification = False

    def __str__(self) -> str:
        return f"AIAssistant(user_message={self.user_message}, system_message={self.system_message}, thread_id={self.thread_id}, new_conversation={self.new_conversation}, response={self.response}, clarify_questions={self.clarify_questions}, need_clarification={self.need_clarification})"

    def start_new_session(self):

        if(self.new_conversation):
            self.thread_id = str(uuid.uuid4())

        return self.thread_id

    
       