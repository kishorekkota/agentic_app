class ChatBot:
    def __init__(self,request:str, response:str,thread_id:str):
        self.response = response
        self.request = request
        self.thread_id = thread_id


    def get_response(self):
        return self.response