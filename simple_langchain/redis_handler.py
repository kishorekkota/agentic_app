import redis
from langgraph.graph import START,END, StateGraph, MessagesState
# Initialize Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

def set_state(thread_id, state):
    redis_client.set(thread_id, state)

def get_state(thread_id):
    return redis_client.get(thread_id)

# StateGraph definition
class RedisStateGraph(StateGraph):
    def save_state(self, thread_id, state):
        set_state(thread_id, state)

    def load_state(self, thread_id):
        return get_state(thread_id)
