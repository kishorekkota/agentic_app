from env_setup import setup_environment
from ai_assistant import AIAssistant

# Set Environment variables before instantiating the class
setup_environment()

# Instantiate the AIAssistant class
assistant = AIAssistant()

# Example usage
user_input = "Can I run outside tomorrow living in 75078? Also let me know next week as well."
response = assistant.run(user_input)
print(response)

user_input = "What's the weather like in 90210 next week?"
response = assistant.run(user_input)
print(response)

user_input = "How about next week?"
assistant.thread_id = "451e87e5f291464c9a235f477c0b8f0a"
assistant.new_conversation = False
response = assistant.run(user_input)
print(response)
print("******** New Conversation ************")

user_input = "what is my first name?"
response = assistant.run(user_input)
print(response)
